const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const SSH_CONFIG = {
    host: '192.168.1.2',
    port: 8022,
    username: 'anything',
    password: '123'
};

const SYNC_DIR = path.join('C:', 'Users', 'anton', 'Sync');
const LOCAL_CHAT = path.join(SYNC_DIR, 'Scripts', 'ai_chat_room.txt');
const LOCAL_AUTH = path.join(SYNC_DIR, '.baileys_auth');
const LOCAL_BRIDGE = path.join(SYNC_DIR, 'Scripts', 'gmc_whatsapp_baileys.js');
const LOCAL_HEARTBEAT = path.join(SYNC_DIR, 'whatsapp_heartbeat.json');

const REMOTE_DIR = 'Sync';
const REMOTE_CHAT = 'Sync/Scripts/ai_chat_room.txt';
const REMOTE_AUTH = 'Sync/.baileys_auth';
const REMOTE_BRIDGE = 'Sync/Scripts/gmc_whatsapp_baileys.js';
const REMOTE_HEARTBEAT = 'Sync/whatsapp_heartbeat.json';

let conn = null;
let sftp = null;
let syncInterval = null;
let isSyncing = false;

console.log('🤖 Запуск GMC SSH/SFTP Синхронизатора...');

function connectSSH() {
    conn = new Client();
    
    conn.on('ready', () => {
        console.log('✅ SSH Подключение установлено успешно!');
        
        conn.sftp((err, sftpSession) => {
            if (err) {
                console.error('❌ Ошибка инициализации SFTP:', err);
                conn.end();
                return;
            }
            sftp = sftpSession;
            console.log('✅ SFTP Сессия открыта!');
            
            // Инициализация структуры папок на телефоне
            setupRemoteStructure(() => {
                // Заливаем свежую версию скрипта моста на телефон
                deployBridgeScript(() => {
                    // Запуск периодической синхронизации
                    startSyncLoop();
                });
            });
        });
    }).on('error', (err) => {
        console.error('❌ Ошибка SSH подключения:', err.message);
        reconnect();
    }).on('close', () => {
        console.log('🔌 SSH соединение закрыто. Переподключение...');
        clearInterval(syncInterval);
        reconnect();
    }).connect(SSH_CONFIG);
}

function reconnect() {
    setTimeout(() => {
        if (!isSyncing) {
            connectSSH();
        }
    }, 5000);
}

// Создание папок на удаленном устройстве
function setupRemoteStructure(callback) {
    const dirs = ['Sync', 'Sync/Scripts', 'Sync/logs', 'Sync/.baileys_auth'];
    let i = 0;
    
    function mkdirNext() {
        if (i >= dirs.length) return callback();
        const dir = dirs[i++];
        sftp.mkdir(dir, (err) => {
            // Игнорируем ошибку, если папка уже существует
            mkdirNext();
        });
    }
    mkdirNext();
}

// Выгрузка актуального скрипта моста на телефон
function deployBridgeScript(callback) {
    console.log('📦 Синхронизация скрипта gmc_whatsapp_baileys.js...');
    sftp.fastPut(LOCAL_BRIDGE, REMOTE_BRIDGE, (err) => {
        if (err) {
            console.error('❌ Не удалось загрузить скрипт моста на телефон:', err);
        } else {
            console.log('✅ Скрипт моста успешно обновлен на телефоне!');
        }
        callback();
    });
}

// Интеллектуальное слияние истории переписки
function mergeChats(localText, remoteText) {
    const localLines = localText.split('\n').map(l => l.trim()).filter(Boolean);
    const remoteLines = remoteText.split('\n').map(l => l.trim()).filter(Boolean);
    
    const mergedLines = [];
    const lineSet = new Set();
    
    // Сначала добавляем все локальные строки
    for (let line of localLines) {
        if (!lineSet.has(line)) {
            lineSet.add(line);
            mergedLines.push(line);
        }
    }
    
    // Добавляем удаленные строки, которых у нас нет
    for (let line of remoteLines) {
        if (!lineSet.has(line)) {
            lineSet.add(line);
            mergedLines.push(line);
        }
    }
    
    return mergedLines.join('\n') + '\n';
}

// Основной цикл синхронизации
function startSyncLoop() {
    if (syncInterval) clearInterval(syncInterval);
    
    syncInterval = setInterval(async () => {
        if (isSyncing || !sftp) return;
        isSyncing = true;
        
        try {
            // 1. Синхронизация файлов сессии .baileys_auth
            await syncAuthSession();
            
            // 1.5. Синхронизация пульса ПК (whatsapp_heartbeat.json)
            await syncHeartbeat();
            
            // 2. Синхронизация ai_chat_room.txt
            await syncChatRoom();
            
            // 3. Контроль запуска моста на телефоне
            await checkAndStartPhoneBridge();
            
        } catch (err) {
            console.error('⚠️ Ошибка в цикле синхронизации:', err);
        } finally {
            isSyncing = false;
        }
    }, 3000);
}

// Функция синхронизации пульса ПК
function syncHeartbeat() {
    return new Promise((resolve) => {
        if (!fs.existsSync(LOCAL_HEARTBEAT)) return resolve();
        
        sftp.fastPut(LOCAL_HEARTBEAT, REMOTE_HEARTBEAT, (err) => {
            if (err) {
                // Игнорируем временные ошибки блокировки при параллельной записи
            }
            resolve();
        });
    });
}

// Функция синхронизации авторизации
function syncAuthSession() {
    return new Promise((resolve) => {
        if (!fs.existsSync(LOCAL_AUTH)) return resolve();
        
        fs.readdir(LOCAL_AUTH, (err, localFiles) => {
            if (err || !localFiles || localFiles.length === 0) return resolve();
            
            sftp.readdir(REMOTE_AUTH, (errRemote, remoteFilesList) => {
                const remoteFiles = errRemote ? [] : remoteFilesList.map(f => f.filename);
                const filesToUpload = localFiles.filter(lf => !remoteFiles.includes(lf));
                
                if (filesToUpload.length === 0) return resolve();
                
                console.log(`🔑 Найдено ${filesToUpload.length} новых файлов авторизации. Выгрузка на телефон...`);
                let uploadedCount = 0;
                
                function uploadNext() {
                    if (uploadedCount >= filesToUpload.length) {
                        console.log('✅ Файлы авторизации синхронизированы!');
                        return resolve();
                    }
                    const filename = filesToUpload[uploadedCount++];
                    const localPath = path.join(LOCAL_AUTH, filename);
                    const remotePath = `${REMOTE_AUTH}/${filename}`;
                    
                    sftp.fastPut(localPath, remotePath, (errPut) => {
                        if (errPut) console.error(`❌ Ошибка загрузки ${filename}:`, errPut);
                        uploadNext();
                    });
                }
                uploadNext();
            });
        });
    });
}

// Функция синхронизации chat_room.txt
function syncChatRoom() {
    return new Promise((resolve) => {
        if (!fs.existsSync(LOCAL_CHAT)) {
            // Если локального файла нет, создаем пустой
            fs.writeFileSync(LOCAL_CHAT, '', 'utf-8');
        }
        
        const localContent = fs.readFileSync(LOCAL_CHAT, 'utf-8');
        const tempRemotePath = path.join(SYNC_DIR, 'Scripts', 'ai_chat_room_remote_temp.txt');
        
        // Скачиваем удаленный файл
        sftp.fastGet(REMOTE_CHAT, tempRemotePath, (errGet) => {
            let remoteContent = '';
            if (!errGet && fs.existsSync(tempRemotePath)) {
                remoteContent = fs.readFileSync(tempRemotePath, 'utf-8');
                fs.unlinkSync(tempRemotePath);
            }
            
            // Если контенты идентичны, ничего не делаем
            if (localContent.trim() === remoteContent.trim()) {
                return resolve();
            }
            
            console.log('🔄 Синхронизация ai_chat_room.txt...');
            const mergedContent = mergeChats(localContent, remoteContent);
            
            // Сохраняем локально
            fs.writeFileSync(LOCAL_CHAT, mergedContent, 'utf-8');
            
            // Заливаем обратно на телефон
            const tempLocalUploadPath = path.join(SYNC_DIR, 'Scripts', 'ai_chat_room_upload_temp.txt');
            fs.writeFileSync(tempLocalUploadPath, mergedContent, 'utf-8');
            
            sftp.fastPut(tempLocalUploadPath, REMOTE_CHAT, (errPut) => {
                if (fs.existsSync(tempLocalUploadPath)) fs.unlinkSync(tempLocalUploadPath);
                if (errPut) {
                    console.error('❌ Ошибка отправки ai_chat_room.txt на телефон:', errPut);
                } else {
                    console.log('✅ Файл ai_chat_room.txt успешно синхронизирован на обоих устройствах!');
                }
                resolve();
            });
        });
    });
}

// Проверка и фоновый перезапуск мобильного моста на телефоне
let lastBridgeCheck = 0;
function checkAndStartPhoneBridge() {
    return new Promise((resolve) => {
        const now = Date.now();
        // Проверяем раз в 15 секунд, чтобы не перегружать SSH
        if (now - lastBridgeCheck < 15000) return resolve();
        lastBridgeCheck = now;
        
        conn.exec('pgrep -f "gmc_whatsapp_baileys.js --node Phone"', (err, stream) => {
            if (err) return resolve();
            
            let output = '';
            stream.on('data', (data) => {
                output += data.toString();
            });
            
            stream.on('close', () => {
                if (output.trim() === '') {
                    console.log('⚠️ Мобильный WhatsApp-мост не запущен на телефоне. Запуск в фоне...');
                    // Запуск через nohup в фоновом режиме
                    conn.exec('nohup node ~/Sync/Scripts/gmc_whatsapp_baileys.js --node Phone > ~/Sync/logs/whatsapp_phone.log 2>&1 &', (errRun, streamRun) => {
                        if (errRun) {
                            console.error('❌ Ошибка запуска мобильного моста:', errRun);
                        } else {
                            console.log('🚀 Команда запуска мобильного моста отправлена на телефон!');
                        }
                        resolve();
                    });
                } else {
                    resolve();
                }
            });
        });
    });
}

// Запуск
connectSSH();
