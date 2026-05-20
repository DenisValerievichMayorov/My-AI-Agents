const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');

const SYNC_DIR = __dirname;
const INBOX_FILE = path.join(SYNC_DIR, 'whatsapp_messages.txt');
const CHAT_FILE = path.join(SYNC_DIR, 'ai_chat_room.txt');

// Глобальные переменные для отслеживания активного чата Дениса и отправленных ИИ ответов
let activeDenisChatId = null;
const sentReplies = new Set();

const LOG_FILE = path.join(SYNC_DIR, 'whatsapp_bridge.log');

// Переопределяем console для синхронного вывода в файл (избегаем буферизации stdout)
const originalLog = console.log;
const originalError = console.error;

console.log = function(...args) {
    originalLog.apply(console, args);
    try {
        const msg = `[${new Date().toLocaleString()}] ` + args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : arg).join(' ') + '\n';
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

console.log('🚀 Starting WhatsApp Bridge script...');

// Инициализация клиента с сохранением сессии
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: false,
        protocolTimeout: 120000,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        ]
    }
});

client.on('qr', (qr) => {
    console.log('--- SCAN THIS QR CODE WITH WHATSAPP ---');
    qrcode.generate(qr, { small: true });
    console.log('Waiting for scan...');
});

client.on('ready', () => {
    console.log('✅ WhatsApp Bridge is READY!');
});

client.on('message_create', async msg => {
    try {
        const chat = await msg.getChat();
        const contact = await msg.getContact();
        const isMe = msg.fromMe;
        
        let mediaInfo = "";
        let filename = "";
        if (msg.hasMedia) {
            try {
                const media = await msg.downloadMedia();
                if (media) {
                    const folder = path.join(SYNC_DIR, 'whatsapp_media');
                    if (!fs.existsSync(folder)) fs.mkdirSync(folder);
                    filename = `${Date.now()}.${media.mimetype.split('/')[1]}`;
                    const filePath = path.join(folder, filename);
                    fs.writeFileSync(filePath, media.data, { encoding: 'base64' });
                    mediaInfo = ` [Media: ${filename}]`;
                }
            } catch (err) {
                console.error('Media download error:', err);
            }
        }

        const sender = isMe ? "Денис (Вы)" : (contact.pushname || contact.number);
        const entry = `[${new Date().toLocaleString()}] ${sender} в чате ${chat.name}: ${msg.body}${mediaInfo}\n`;
        
        console.log('WhatsApp Event:', entry.trim());
        fs.appendFileSync(INBOX_FILE, entry);

        // Интеграция с ИИ: Общение ТОЛЬКО с Денисом в его личном чате (Self-Chat или Сын / Сын (Вы))
        const isSelfChat = (chat.id._serialized === client.info.wid._serialized) || 
                           (chat.name === "Денис (Вы)") || 
                           (chat.name === "Денис") || 
                           (chat.name === "Сын") || 
                           (chat.name === "Сын (Вы)");
                           
        const isBotReply = msg.body.startsWith('[WhatsApp Reply]:') || msg.body.startsWith('GMC:') || msg.body.includes('Sent WhatsApp Reply');
        
        // Предотвращение бесконечного цикла: если это сообщение было отправлено самим ботом
        const cleanMsg = msg.body.trim();
        if (sentReplies.has(cleanMsg)) {
            sentReplies.delete(cleanMsg);
            console.log(`ℹ️ Ignoring our own sent message to prevent loop: "${cleanMsg}"`);
            return;
        }

        if (!chat.isGroup && !isBotReply && msg.body.trim()) {
            console.log(`🤖 Triggering AI response/monitoring in chat: ${chat.name}...`);
            activeDenisChatId = chat.id._serialized; // Запоминаем ID чата, куда нужно ответить
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
                eventLine = `\n[${timestamp}] [System Event]: WhatsApp от Дениса: ${msg.body}${mediaPrompt} (Пожалуйста, ответь Денису в WhatsApp. Твой ответ должен начинаться строго с '[WhatsApp Reply]: ')\n`;
            } else {
                eventLine = `\n[${timestamp}] [System Event]: Новое сообщение в WhatsApp от ${sender} (чат ${chat.name}): ${msg.body}${mediaPrompt} (Пожалуйста, проанализируй сообщение в контексте всей переписки. Если оно требует внимания Дениса, самостоятельно подготовь нужную информацию, проверь календарь или документы через !google/!run, и составь краткое проактивное уведомление для Дениса. Оно должно начинаться строго с '[WhatsApp Reply]: [ИИ Уведомление]: ')\n`;
            }
            fs.appendFileSync(CHAT_FILE, eventLine);
        }
    } catch (e) {
        console.error('Error in message_create:', e);
    }
});

// Мониторинг ai_chat_room.txt для отправки исходящих ответов ИИ Денису
setInterval(async () => {
    try {
        if (fs.existsSync(CHAT_FILE)) {
            let content = fs.readFileSync(CHAT_FILE, 'utf-8');
            if (content.includes('[WhatsApp Reply]:')) {
                let lines = content.split('\n');
                let updatedLines = [];
                let repliesToSend = [];

                for (let line of lines) {
                    // Парсим только реальные ответы ИИ, игнорируя системные промпты с этой строкой
                    if (line.includes('[WhatsApp Reply]:') && !line.includes('[System Event]:')) {
                        let parts = line.split('[WhatsApp Reply]:');
                        if (parts.length > 1) {
                            repliesToSend.push(parts[1].trim());
                        }
                    } else {
                        updatedLines.push(line);
                    }
                }

                // Записываем файл обратно БЕЗ строк ответов ИИ, чтобы избежать дублей
                fs.writeFileSync(CHAT_FILE, updatedLines.join('\n'), 'utf-8');

                // Отправляем собранные ответы Денису в WhatsApp
                if (repliesToSend.length > 0 && client.info) {
                    // Отправляем обратно в тот же чат, где Денис задал вопрос, либо в Self-Chat по умолчанию
                    const targetChatId = activeDenisChatId || client.info.wid._serialized;
                    for (let reply of repliesToSend) {
                        if (reply) {
                            sentReplies.add(reply.trim()); // Сохраняем в памяти, чтобы проигнорировать в message_create
                            await client.sendMessage(targetChatId, reply);
                            console.log(`✅ Sent WhatsApp Reply to chat (${targetChatId}): ${reply}`);
                        }
                    }
                }
            }
        }
    } catch (e) {
        console.error('Outbox monitor error:', e);
    }
}, 3000);

client.initialize();
