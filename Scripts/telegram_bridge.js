const TelegramBot = require('node-telegram-bot-api');
const fs = require('fs');
const path = require('path');
const os = require('os');

// --- Конфигурация ---
const TOKEN = '8309646654:AAEHGEU2idhWV4OJPmH_-2m8rs3-HPNM6ew';
const ALLOWED_USER_ID = 6494450623; // Denis Maiorov

// Автоопределение путей
const IS_TERMUX = process.env.TERMUX_VERSION !== undefined || fs.existsSync('/data/data/com.termux/files/usr/bin/bash');
const BASE_SYNC_DIR = IS_TERMUX 
    ? '/data/data/com.termux/files/home/sync/scripts' 
    : path.join(os.homedir(), 'Sync', 'scripts');

const CHAT_FILE = path.join(BASE_SYNC_DIR, 'ai_chat_room.txt');
const LOG_FILE = path.join(BASE_SYNC_DIR, 'telegram_bridge.log');

function log(msg) {
    const entry = `[${new Date().toLocaleString()}] ${msg}\n`;
    console.log(entry.trim());
    try {
        fs.appendFileSync(LOG_FILE, entry);
    } catch (e) {}
}

log(`🚀 Запуск Telegram Bridge на ${IS_TERMUX ? 'Termux' : 'PC/Chromebook'}...`);

const bot = new TelegramBot(TOKEN, { polling: true });

// Переменная для отслеживания последнего сообщения от ИИ, чтобы избежать дублей
let lastProcessedLine = null;

// Обработка входящих сообщений
bot.on('message', (msg) => {
    const chatId = msg.chat.id;
    const text = msg.text;

    if (chatId !== ALLOWED_USER_ID) {
        log(`⚠️ Попытка доступа от неизвестного пользователя: ${chatId} (${msg.from.username})`);
        return;
    }

    if (!text) return;

    log(`📩 Получено из Telegram: ${text}`);

    const now = new Date();
    const timestamp = now.getFullYear() + '-' +
                      String(now.getMonth() + 1).padStart(2, '0') + '-' +
                      String(now.getDate()).padStart(2, '0') + ' ' +
                      String(now.getHours()).padStart(2, '0') + ':' +
                      String(now.getMinutes()).padStart(2, '0') + ':' +
                      String(now.getSeconds()).padStart(2, '0');

    // Формат System Event, который понимает agent_listener.py
    const eventLine = `\n[${timestamp}] [System Event]: Telegram от Дениса: ${text} (Пожалуйста, ответь Денису в Telegram. Твой ответ должен начинаться строго с '[WhatsApp Reply]: ')\n`;
    
    try {
        fs.appendFileSync(CHAT_FILE, eventLine);
        log(`✅ Записано в ai_chat_room.txt`);
    } catch (e) {
        log(`❌ Ошибка записи в файл чата: ${e.message}`);
    }
});

// Мониторинг ответов ИИ в ai_chat_room.txt
setInterval(() => {
    try {
        if (fs.existsSync(CHAT_FILE)) {
            const content = fs.readFileSync(CHAT_FILE, 'utf-8');
            const lines = content.split('\n').filter(line => line.trim() !== '');
            if (lines.length === 0) return;

            const lastLine = lines[lines.length - 1];

            // Проверяем, является ли это ответом ИИ (префикс [WhatsApp Reply]: навязан сервером)
            if (lastLine.includes('[WhatsApp Reply]:') && lastLine !== lastProcessedLine) {
                // Избегаем срабатывания на системные промпты
                if (lastLine.includes('[System Event]:')) return;

                log(`🤖 Обнаружен ответ ИИ: ${lastLine}`);
                
                // Очищаем текст от префикса
                let replyText = lastLine.split('[WhatsApp Reply]:')[1].trim();
                
                // Если в ответе есть имя устройства [DESKTOP-...]:, убираем его для красоты
                if (replyText.includes(']:')) {
                    replyText = replyText.split(']:').slice(1).join(']:').trim();
                }

                bot.sendMessage(ALLOWED_USER_ID, replyText)
                    .then(() => {
                        log(`✅ Ответ отправлен в Telegram`);
                        lastProcessedLine = lastLine;
                    })
                    .catch((err) => {
                        log(`❌ Ошибка отправки в Telegram: ${err.message}`);
                    });
            }
        }
    } catch (e) {
        log(`❌ Ошибка мониторинга чата: ${e.message}`);
    }
}, 2000);

bot.on('polling_error', (error) => {
    log(`⚠️ Ошибка Telegram Polling: ${error.code} - ${error.message}`);
});

log('✅ Мост Telegram готов и слушает сообщения.');
