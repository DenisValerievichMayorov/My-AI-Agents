const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');

const SYNC_DIR = __dirname;
const INBOX_FILE = path.join(SYNC_DIR, 'whatsapp_messages.txt');
const OUTBOX_FILE = path.join(SYNC_DIR, 'whatsapp_outbox.txt');

// Инициализация клиента с сохранением сессии
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox']
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
    const chat = await msg.getChat();
    const contact = await msg.getContact();
    const isMe = msg.fromMe;
    
    let mediaInfo = "";
    if (msg.hasMedia) {
        try {
            const media = await msg.downloadMedia();
            if (media) {
                const folder = path.join(SYNC_DIR, 'whatsapp_media');
                if (!fs.existsSync(folder)) fs.mkdirSync(folder);
                const filename = `${Date.now()}.${media.mimetype.split('/')[1]}`;
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
    
    console.log('WhatsApp Event:', entry);
    fs.appendFileSync(INBOX_FILE, entry);
});

// Проверка исходящих сообщений каждые 5 секунд
setInterval(async () => {
    if (fs.existsSync(OUTBOX_FILE)) {
        const content = fs.readFileSync(OUTBOX_FILE, 'utf-8').trim();
        if (content) {
            try {
                const [target, ...textParts] = content.split(':');
                const text = textParts.join(':').strip();
                // target может быть именем контакта или номером
                // Для простоты пока логируем, отправка требует поиска chatID
                console.log(`Need to send to ${target}: ${text}`);
                // fs.unlinkSync(OUTBOX_FILE); // Удаляем после обработки
            } catch (e) {
                console.error('Outbox error:', e);
            }
        }
    }
}, 5000);

client.initialize();
