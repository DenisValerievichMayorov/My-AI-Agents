const { 
    default: makeWASocket, 
    useMultiFileAuthState, 
    downloadMediaMessage,
    fetchLatestBaileysVersion
} = require('@whiskeysockets/baileys');
const fs = require('fs');
const path = require('path');
const pino = require('pino');

const SYNC_DIR = path.join('/data/data/com.termux/files/home', 'Sync');
const AUTH_DIR = path.join(SYNC_DIR, '.baileys_auth');
const MEDIA_DIR = path.join(SYNC_DIR, 'whatsapp_media');

async function fetchMedia() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    const { version } = await fetchLatestBaileysVersion();
    
    const logger = pino({ level: 'silent' });
    const sock = makeWASocket({
        version,
        auth: state,
        logger,
        printQRInTerminal: false,
        syncFullHistory: false // Мы не хотим тянуть все, только то что придет
    });

    sock.ev.on('creds.update', saveCreds);

    console.log('⏳ Подключаюсь и жду событий истории (30 секунд)...');

    // Слушаем все сообщения, которые могут прийти при синхронизации
    sock.ev.on('messages.upsert', async m => {
        for (const msg of m.messages) {
            const messageType = Object.keys(msg.message || {})[0];
            const hasMedia = ['imageMessage', 'documentMessage', 'audioMessage', 'videoMessage'].includes(messageType);
            
            if (hasMedia) {
                const timestamp = msg.messageTimestamp;
                const sender = msg.pushName || msg.key.remoteJid;
                console.log(`📸 Найдено медиа от ${sender} [${new Date(timestamp * 1000).toLocaleString()}]`);
                
                try {
                    const buffer = await downloadMediaMessage(msg, 'buffer', {}, { logger });
                    if (buffer) {
                        let ext = 'bin';
                        if (messageType === 'imageMessage') ext = 'jpg';
                        const filename = `history_${timestamp}_${msg.key.id}.${ext}`;
                        const filePath = path.join(MEDIA_DIR, filename);
                        
                        if (!fs.existsSync(filePath)) {
                            fs.writeFileSync(filePath, buffer);
                            console.log(`✅ Сохранено: ${filename}`);
                        }
                    }
                } catch (e) {
                    console.error('Ошибка загрузки:', e.message);
                }
            }
        }
    });

    // Слушаем специальное событие установки истории
    sock.ev.on('messaging-history.set', async ({ messages }) => {
        console.log(`📥 Получена порция истории: ${messages.length} сообщений.`);
        for (const msg of messages) {
            const messageType = Object.keys(msg.message || {})[0];
            if (messageType === 'imageMessage') {
                console.log(`🖼️ Найдено фото в истории от ${msg.pushName || msg.key.remoteJid}`);
                try {
                    const buffer = await downloadMediaMessage(msg, 'buffer', {}, { logger });
                    if (buffer) {
                        const filename = `history_sync_${msg.messageTimestamp}_${msg.key.id}.jpg`;
                        const filePath = path.join(MEDIA_DIR, filename);
                        if (!fs.existsSync(filePath)) {
                            fs.writeFileSync(filePath, buffer);
                            console.log(`✅ Сохранено из истории: ${filename}`);
                        }
                    }
                } catch (e) {}
            }
        }
    });

    setTimeout(() => {
        console.log('⏰ Время ожидания истекло. Завершаю.');
        process.exit(0);
    }, 30000);
}

fetchMedia().catch(err => {
    console.error('Ошибка:', err);
    process.exit(1);
});
