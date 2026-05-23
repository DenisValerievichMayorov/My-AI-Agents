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
const TARGET_JID = '118979670634534@s.whatsapp.net'; // Чат со Светланой

async function fetchMedia() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    const { version } = await fetchLatestBaileysVersion();
    
    const logger = pino({ level: 'silent' });
    const sock = makeWASocket({
        version,
        auth: state,
        logger,
        printQRInTerminal: false
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
        const { connection } = update;
        if (connection === 'open') {
            console.log('✅ Подключено! Начинаю поиск медиа в истории...');
            
            try {
                // Запрашиваем последние сообщения
                const messages = await sock.fetchMessagesFromChat(TARGET_JID, 20);
                console.log(`Найдено ${messages.length} сообщений в истории.`);

                if (!fs.existsSync(MEDIA_DIR)) fs.mkdirSync(MEDIA_DIR, { recursive: true });

                for (const msg of messages) {
                    const messageType = Object.keys(msg.message || {})[0];
                    const hasMedia = ['imageMessage', 'documentMessage', 'audioMessage', 'videoMessage'].includes(messageType);
                    
                    if (hasMedia) {
                        const timestamp = msg.messageTimestamp;
                        const dateStr = new Date(timestamp * 1000).toLocaleString();
                        
                        console.log(`[${dateStr}] Найдено медиа: ${messageType}`);
                        
                        try {
                            const buffer = await downloadMediaMessage(msg, 'buffer', {}, { logger });
                            if (buffer) {
                                let ext = 'bin';
                                if (messageType === 'imageMessage') ext = 'jpg';
                                else if (messageType === 'audioMessage') ext = 'ogg';
                                else if (messageType === 'documentMessage') ext = 'pdf';
                                
                                const filename = `forced_${timestamp}.${ext}`;
                                const filePath = path.join(MEDIA_DIR, filename);
                                
                                if (!fs.existsSync(filePath)) {
                                    fs.writeFileSync(filePath, buffer);
                                    console.log(`✅ Скачано: ${filename}`);
                                } else {
                                    console.log(`ℹ️ Файл уже существует: ${filename}`);
                                }
                            }
                        } catch (err) {
                            console.error('Ошибка загрузки медиа:', err.message);
                        }
                    }
                }
            } catch (err) {
                console.error('Ошибка получения истории:', err);
            }

            console.log('🏁 Процесс завершен. Закрываю соединение.');
            process.exit(0);
        }
    });
}

fetchMedia().catch(err => {
    console.error('Критическая ошибка:', err);
    process.exit(1);
});
