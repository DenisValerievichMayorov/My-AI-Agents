const { Client } = require('ssh2');

const conn = new Client();

const config = {
    host: '192.168.1.2',
    port: 8022,
    username: 'anything',
    password: '123'
};

const cmd = process.argv[2] || 'uname -a; pkg list-installed | grep rclone';

conn.on('ready', () => {
    conn.exec(cmd, (err, stream) => {
        if (err) throw err;
        
        let stdout = '';
        let stderr = '';
        
        stream.on('close', (code, signal) => {
            console.log(stdout);
            if (stderr) console.error(stderr);
            conn.end();
        }).on('data', (data) => {
            stdout += data.toString();
        }).stderr.on('data', (data) => {
            stderr += data.toString();
        });
    });
}).on('error', (err) => {
    console.error('SSH Error:', err.message);
    process.exit(1);
}).connect(config);
