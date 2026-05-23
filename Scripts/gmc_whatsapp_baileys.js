const { 
    default: makeWASocket, 
    useMultiFileAuthState, 
    DisconnectReason,
    downloadMediaMessage,
    fetchLatestBaileysVersion
} = require('@whiskeysockets/baileys');
const fs = require('fs');
const path = require('path');
const qrcode = require('qrcode-terminal');
const pino = require('pino');

// Пути к файлам и папкам
const isWindows = process.platform === 'win32';
const SYNC_DIR = isWindows 
    ? path.join('C:', 'Users', 'anton', 'Sync')
    : path.join(process.env.HOME || '/data/data/com.termux/files/home', 'Sync');

const SCRIPTS_DIR = path.join(SYNC_DIR, 'Scripts');
const CHAT_FILE = path.join(SYNC_DIR, 'Scripts', 'ai_chat_room.txt');
const INBOX_FILE = path.join(SYNC_DIR, 'logs', 'whatsapp_messages.txt');
const LOG_FILE = path.join(SYNC_DIR, 'logs', 'whatsapp_baileys.log');
const HEARTBEAT_FILE = path.join(SYNC_DIR, 'whatsapp_heartbeat.json');
const AUTH_DIR = path.join(SYNC_DIR, '.baileys_auth');

// Настройка логирования в файл и консоль
const logger = pino({ level: 'silent' });
const originalLog = console.log;
const originalError = console.error;

console.log = function(...args) {
    originalLog.apply(console, args);
    try {
        const msg = `[${new Date().toLocaleString()}] [INFO] ` + args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : arg).join(' ') + '\n';
        fs.appendFileSync(LOG_FILE, msg);
    } catch(e) {}
};

console.error = function(...args) {
    originalError.apply(console, args);
    try {
        const msg = `[${new Date().toLocaleString()}] [ERROR] ` + args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : arg).join(' ') + '\n';
        fs.appendFileSync(LOG_FILE, msg);
    } catch(e) {}
};

// Определение имени текущего узла (PC или Phone)
const nodeName = process.argv.includes('--node') 
    ? process.argv[process.argv.indexOf('--node') + 1] 
    : 'UnknownNode';

console.log(`🚀 Запуск WhatsApp Baileys Bridge на узле: ${nodeName}...`);

let sock = null;
let forceDisconnect = false;
let isActive = false;
let activeDenisChatId = null;
const sentReplies = new Set();


// Функция управления кластерным пульсом (Active-Passive)
function updateHeartbeat() {
    try {
        let pcOnline = false;
        if (fs.existsSync(HEARTBEAT_FILE)) {
            try {
                const hb = JSON.parse(fs.readFileSync(HEARTBEAT_FILE, 'utf-8'));
                // Если запись от ПК и она свежая (менее 45 секунд)
                if (hb.active_node === 'PC' && (Date.now() - hb.heartbeat) < 45000) {
                    pcOnline = true;
                }
            } catch(e) {}
        }

        if (nodeName === 'PC') {
            isActive = true;
            fs.writeFileSync(HEARTBEAT_FILE, JSON.stringify({
                active_node: 'PC',
                heartbeat: Date.now()
            }, null, 2), 'utf-8');
        } else {
            // Если мы телефон, то активны только если ПК оффлайн
            if (pcOnline) {
                if (isActive) {
                    console.log(`[Cluster] ПК в сети. Переключаю телефонный узел ${nodeName} в режим ожидания (Standby).`);
                }
                isActive = false;
                
                // Если сокет активен, закрываем его для предотвращения конфликта
                if (sock) {
                    console.log(`[Cluster] Закрываем локальное подключение к WhatsApp на телефоне, так как ПК активен.`);
                    forceDisconnect = true;
                    try {
                        sock.ws.close();
                    } catch (e) {}
                    sock = null;
                }
            } else {
                if (!isActive) {
                    console.log(`[Cluster] ПК оффлайн или не отвечает. Активирую телефонный узел ${nodeName} как основной ответчик!`);
                }
                isActive = true;
                fs.writeFileSync(HEARTBEAT_FILE, JSON.stringify({
                    active_node: nodeName,
                    heartbeat: Date.now()
                }, null, 2), 'utf-8');
                
                // Если сокет не активен, подключаем его
                if (!sock) {
                    console.log(`[Cluster] Инициализируем подключение к WhatsApp на телефоне...`);
                    forceDisconnect = false;
                    startWhatsApp().catch(err => console.error("Ошибка автозапуска WhatsApp на телефоне:", err));
                }
            }
        }
    } catch (err) {
        console.error('Ошибка обновления пульса:', err);
    }
}

// Запуск интервала пульса (каждые 15 секунд)
updateHeartbeat();
setInterval(updateHeartbeat, 15000);

async function startWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    
    let version;
    try {
        const latest = await fetchLatestBaileysVersion();
        version = latest.version;
        console.log(`🔎 Определена последняя версия WhatsApp Web: ${version.join('.')}`);
    } catch (err) {
        console.error("⚠️ Не удалось получить актуальную версию WhatsApp Web, используем встроенную в библиотеку:", err);
    }
    
    sock = makeWASocket({
        version,
        auth: state,
        logger,
        printQRInTerminal: false // Отключаем стандартный вывод, выведем красиво
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        
        if (qr) {
            console.log('--- ОТСКАНИРУЙТЕ ЭТОТ QR-КОД В WHATSAPP ---');
            qrcode.generate(qr, { small: true });
            console.log('Ожидание сканирования...');
            
            // Создаем красивый HTML-файл с автообновлением для удобного сканирования в браузере
            try {
                const htmlPath = path.join(SYNC_DIR, 'whatsapp_qr.html');
                const htmlContent = `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>WhatsApp Web QR Code</title>
    <style>
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            background: #0b141a;
            color: #e9edef;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
        }
        .card {
            background: #111b21;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            text-align: center;
            max-width: 420px;
            border: 1px solid #222e35;
        }
        h2 {
            color: #00a884;
            margin-top: 0;
            font-weight: 500;
        }
        .qr-container {
            background: white;
            padding: 24px;
            border-radius: 12px;
            display: inline-block;
            margin: 25px 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        p {
            color: #8696a0;
            font-size: 15px;
            line-height: 1.4;
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
</head>
<body>
    <div class="card">
        <h2>WhatsApp GMC Bridge</h2>
        <p>Отсканируйте этот QR-код через WhatsApp на телефоне для подключения ИИ-агентов</p>
        <div class="qr-container" id="qrcode"></div>
        <p style="font-size: 13px; color: #667781;">Страница автоматически обновляется при получении нового кода.</p>
    </div>
    <script>
        new QRCode(document.getElementById("qrcode"), {
            text: "${qr}",
            width: 256,
            height: 256,
            colorDark : "#000000",
            colorLight : "#ffffff",
            correctLevel : QRCode.CorrectLevel.H
        });
        setTimeout(() => {
            window.location.reload();
        }, 15000);
    </script>
</body>
</html>`;
                fs.writeFileSync(htmlPath, htmlContent, 'utf-8');
                console.log(`ℹ️ Красивый QR-код для браузера сохранен в: ${htmlPath}`);
            } catch (err) {
                console.error('Ошибка записи html QR-кода:', err);
            }
        }
        
        if (connection === 'close') {
            const isStandbyClose = forceDisconnect;
            const shouldReconnect = (lastDisconnect.error)?.output?.statusCode !== DisconnectReason.loggedOut && !isStandbyClose;
            console.log('❌ Соединение закрыто из-за:', lastDisconnect.error, '. Повторное подключение:', shouldReconnect);
            if (shouldReconnect) {
                setTimeout(startWhatsApp, 5000);
            }
        } else if (connection === 'open') {
            console.log('✅ WhatsApp Baileys Bridge успешно запущен и ГОТОВ к работе!');
            
            // Удаляем временный файл QR-кода или пишем статус успеха
            try {
                const htmlPath = path.join(SYNC_DIR, 'whatsapp_qr.html');
                if (fs.existsSync(htmlPath)) {
                    fs.writeFileSync(htmlPath, `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>WhatsApp Connected</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #0b141a;
            color: #e9edef;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
        }
        .card {
            background: #111b21;
            padding: 40px;
            border-radius: 16px;
            text-align: center;
            border: 1px solid #222e35;
        }
        h2 { color: #00a884; }
    </style>
</head>
<body>
    <div class="card">
        <h2>✅ Успешно авторизовано!</h2>
        <p>WhatsApp мост активен и синхронизируется с телефоном.</p>
    </div>
</body>
</html>`, 'utf-8');
                }
            } catch(e) {}
        }
    });

    // Обработка входящих сообщений
    sock.ev.on('messages.upsert', async m => {
        if (m.type !== 'notify') return;
        
        for (const msg of m.messages) {
            try {
                if (!msg.message) continue;
                const remoteJid = msg.key.remoteJid;
                
                // Пропускаем групповые чаты и рассылки, обрабатываем только личные диалоги
                if (remoteJid.endsWith('@g.us') || remoteJid.endsWith('@broadcast')) continue;
                
                const isMe = msg.key.fromMe;
                const messageType = Object.keys(msg.message)[0];
                
                // Извлекаем текст
                let body = "";
                if (messageType === 'conversation') {
                    body = msg.message.conversation;
                } else if (messageType === 'extendedTextMessage') {
                    body = msg.message.extendedTextMessage.text;
                } else if (messageType === 'imageMessage') {
                    body = msg.message.imageMessage.caption || "";
                } else if (messageType === 'documentMessage') {
                    body = msg.message.documentMessage.title || "";
                }

                body = body.trim();
                if (!body && !msg.message.imageMessage && !msg.message.audioMessage) continue;

                // Запоминаем ID последнего чата с Денисом
                activeDenisChatId = remoteJid;

                // Обработка медиафайлов
                let mediaInfo = "";
                let filename = "";
                const hasMedia = ['imageMessage', 'documentMessage', 'audioMessage', 'videoMessage'].includes(messageType);
                
                if (hasMedia) {
                    try {
                        const buffer = await downloadMediaMessage(msg, 'buffer', {}, { logger });
                        if (buffer) {
                            const folder = path.join(SYNC_DIR, 'whatsapp_media');
                            if (!fs.existsSync(folder)) fs.mkdirSync(folder, { recursive: true });
                            
                            let ext = 'bin';
                            if (messageType === 'imageMessage') ext = 'jpg';
                            else if (messageType === 'audioMessage') ext = 'ogg';
                            else if (messageType === 'documentMessage') ext = 'pdf';
                            
                            filename = `${Date.now()}.${ext}`;
                            const filePath = path.join(folder, filename);
                            fs.writeFileSync(filePath, buffer);
                            mediaInfo = ` [Media: ${filename}]`;
                        }
                    } catch (err) {
                        console.error('Ошибка загрузки медиафайла:', err);
                    }
                }

                const senderName = isMe ? "Денис (Вы)" : (msg.pushName || remoteJid.split('@')[0]);
                const msgId = msg.key.id;
                const entry = `[${new Date().toLocaleString()}] [ID: ${msgId}] ${senderName}: ${body}${mediaInfo}\n`;
                
                console.log(`WhatsApp Event (ID: ${msgId}):`, entry.trim());
                
                // Записываем в лог входящих сообщений
                const logsFolder = path.join(SYNC_DIR, 'logs');
                if (!fs.existsSync(logsFolder)) fs.mkdirSync(logsFolder, { recursive: true });
                fs.appendFileSync(INBOX_FILE, entry);

                // Предотвращение бесконечного цикла
                if (sentReplies.has(body)) {
                    sentReplies.delete(body);
                    console.log(`ℹ️ Игнорируем собственное отправленное сообщение: "${body}"`);
                    continue;
                }

                const isBotReply = body.startsWith('[WhatsApp Reply]:') || body.startsWith('GMC:') || body.includes('Sent WhatsApp Reply');
                
                if (!isBotReply && (body || filename)) {
                    console.log(`🤖 Отправляем событие в ai_chat_room.txt для ИИ...`);
                    const mediaPrompt = filename ? ` [Media: ${filename}]` : "";
                    const now = new Date();
                    const timestamp = now.getFullYear() + '-' + 
                                      String(now.getMonth() + 1).padStart(2, '0') + '-' + 
                                      String(now.getDate()).padStart(2, '0') + ' ' + 
                                      String(now.getHours()).padStart(2, '0') + ':' + 
                                      String(now.getMinutes()).padStart(2, '0') + ':' + 
                                      String(now.getSeconds()).padStart(2, '0');
                                      
                    let eventLine = "";
                    if (isMe) {
                        eventLine = `\n[${timestamp}] [System Event]: WhatsApp от Дениса: ${body}${mediaPrompt} (Пожалуйста, ответь Денису в WhatsApp. Твой ответ должен начинаться строго с '[WhatsApp Reply]: ')\n`;
                    } else {
                        eventLine = `\n[${timestamp}] [System Event]: Новое сообщение в WhatsApp от ${senderName} (чат ${remoteJid.split('@')[0]}): ${body}${mediaPrompt} (Пожалуйста, проанализируй сообщение в контексте всей переписки. Если оно требует внимания Дениса, самостоятельно подготовь нужную информацию и составь краткое проактивное уведомление для Дениса. Оно должно начинаться строго с '[WhatsApp Reply]: [ИИ Уведомление]: ')\n`;
                    }
                    fs.appendFileSync(CHAT_FILE, eventLine);
                }

            } catch (err) {
                console.error('Ошибка разбора сообщения:', err);
            }
        }
    });

    /* 
    // Мониторинг файла ai_chat_room.txt для отправки исходящих сообщений ИИ (ОТКЛЮЧЕНО ПО ПРОСЬБЕ ДЕНИСА)
    setInterval(async () => {
        try {
            if (!isActive) return; // Если мы в режиме ожидания (Standby), то ничего не отправляем

            if (fs.existsSync(CHAT_FILE)) {
                let content = fs.readFileSync(CHAT_FILE, 'utf-8');
                if (content.includes('[WhatsApp Reply]:')) {
                    let lines = content.split('\n');
                    let updatedLines = [];
                    let repliesToSend = [];

                    for (let line of lines) {
                        if (line.includes('[WhatsApp Reply]:') && !line.includes('[System Event]:')) {
                            let parts = line.split('[WhatsApp Reply]:');
                            if (parts.length > 1) {
                                repliesToSend.push(parts[1].trim());
                            }
                        } else {
                            updatedLines.push(line);
                        }
                    }

                    // Перезаписываем файл БЕЗ отправленных ответов, чтобы избежать дублирования
                    fs.writeFileSync(CHAT_FILE, updatedLines.join('\n'), 'utf-8');

                    // Отправляем ответы
                    if (repliesToSend.length > 0) {
                        const targetChatId = activeDenisChatId || (sock.user && sock.user.id ? sock.user.id.split(':')[0] + '@s.whatsapp.net' : null);
                        if (targetChatId) {
                            for (let reply of repliesToSend) {
                                if (reply) {
                                    sentReplies.add(reply.trim());
                                    await sock.sendMessage(targetChatId, { text: reply });
                                    console.log(`✅ [${nodeName}] Отправлен ответ в WhatsApp (${targetChatId}): ${reply}`);
                                }
                            }
                        } else {
                            console.log('ℹ️ Ожидание авторизации WhatsApp для отправки исходящих ответов...');
                            // Восстанавливаем исходное содержимое файла, чтобы не потерять сообщения ИИ
                            fs.writeFileSync(CHAT_FILE, content, 'utf-8');
                        }
                    }
                }
            }
        } catch (err) {
            console.error('Ошибка мониторинга исходящих сообщений:', err);
        }
    }, 3000);
    */
}

if (nodeName === 'PC') {
    startWhatsApp().catch(err => console.error("Критическая ошибка запуска PC:", err));
} else {
    console.log(`[Cluster] Узел Phone запущен в режиме ожидания (Standby).`);
}
