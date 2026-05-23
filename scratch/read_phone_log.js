const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();
const config = {
    host: '192.168.1.2',
    port: 8022,
    username: 'anything',
    password: '123'
};

conn.on('ready', () => {
    conn.sftp((err, sftp) => {
        if (err) throw err;
        
        const remoteLogPath = 'Sync/logs/whatsapp_phone.log';
        const localLogPath = path.join('C:', 'Users', 'anton', 'Sync', 'logs', 'whatsapp_phone_remote.log');
        
        console.log('Fetching remote log...');
        sftp.fastGet(remoteLogPath, localLogPath, (errGet) => {
            if (errGet) {
                console.error('Error fetching log:', errGet);
                conn.end();
                return;
            }
            
            console.log('Log fetched successfully! Content:\n');
            const content = fs.readFileSync(localLogPath, 'utf-8');
            console.log(content);
            
            if (fs.existsSync(localLogPath)) fs.unlinkSync(localLogPath);
            conn.end();
        });
    });
}).on('error', (err) => {
    console.error('Connection error:', err);
}).connect(config);
