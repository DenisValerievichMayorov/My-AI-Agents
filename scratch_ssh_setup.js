const { Client } = require('ssh2');

const conn = new Client();

const config = {
    host: '192.168.1.2',
    port: 8022,
    username: 'anything',
    password: '123'
};

conn.on('ready', () => {
    console.log('✅ SSH Connection Ready!');
    
    // Смотрим логи Syncthing на телефоне
    const cmd = `
        echo "=== PHONE SYNCTHING LOGS ==="
        tail -n 20 ~/syncthing.log
    `;
    
    conn.exec(cmd, (err, stream) => {
        if (err) throw err;
        
        let stdout = '';
        let stderr = '';
        
        stream.on('close', (code, signal) => {
            console.log(`Stream closed with code ${code}`);
            console.log('STDOUT:\n', stdout);
            console.log('STDERR:\n', stderr);
            conn.end();
        }).on('data', (data) => {
            stdout += data.toString();
        }).stderr.on('data', (data) => {
            stderr += data.toString();
        });
    });
}).on('error', (err) => {
    console.error('❌ Connection Error:', err);
}).connect(config);
