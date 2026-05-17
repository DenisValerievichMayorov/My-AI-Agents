const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');

const SYNC_DIR = __dirname;
const INBOX_FILE = path.join(SYNC_DIR, 'whatsapp_messages.txt');
const CHAT_FILE = path.join(SYNC_DIR, 'ai_chat_room.txt');

// Инициализация клиента с сохранением сессии
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
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

        // Интеграция с ИИ: Общение ТОЛЬКО с Денисом в его личном чате (Self-Chat)
        const isSelfChat = (chat.id._serialized === client.info.wid._serialized) || (chat.name === "Денис (Вы)") || (chat.name === "Денис");
        const isBotReply = msg.body.startsWith('[WhatsApp Reply]:') || msg.body.startsWith('GMC:') || msg.body.includes('Sent WhatsApp Reply');

        if (isSelfChat && isMe && !isBotReply && msg.body.trim()) {
            console.log('🤖 Triggering AI response for Denis...');
            const mediaPrompt = filename ? ` [Media: ${filename}]` : "";
            const eventLine = `\n[System Event]: WhatsApp от Дениса: ${msg.body}${mediaPrompt} (Пожалуйста, ответь Денису в WhatsApp. Твой ответ должен начинаться строго с '[WhatsApp Reply]: ')\n`;
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
                    if (line.includes('[WhatsApp Reply]:')) {
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
                    const myChatId = client.info.wid._serialized;
                    for (let reply of repliesToSend) {
                        if (reply) {
                            await client.sendMessage(myChatId, reply);
                            console.log(`✅ Sent WhatsApp Reply to Denis: ${reply}`);
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
