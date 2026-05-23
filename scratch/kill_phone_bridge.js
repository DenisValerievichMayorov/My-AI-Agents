const { Client } = require('ssh2');

const conn = new Client();
const config = {
    host: '192.168.1.2',
    port: 8022,
    username: 'anything',
    password: '123'
};

conn.on('ready', () => {
    console.log('✅ SSH Ready!');
    
    console.log('Killing old Phone bridge process...');
    conn.exec('pkill -f "gmc_whatsapp_baileys.js --node Phone"', (err, stream) => {
        if (err) throw err;
        
        stream.on('close', (code) => {
            console.log(`pkill finished with code ${code}`);
            
            // Проверим, что процессы убиты
            conn.exec('pgrep -f "gmc_whatsapp_baileys.js --node Phone"', (err2, stream2) => {
                let output = '';
                stream2.on('data', (d) => output += d.toString());
                stream2.on('close', () => {
                    console.log('Remaining processes:', output.trim() || 'None');
                    conn.end();
                });
            });
        }).on('data', (data) => {
            process.stdout.write(data.toString());
        });
    });
}).on('error', (err) => {
    console.error('Connection error:', err);
}).connect(config);
