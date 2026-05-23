const { Client } = require('ssh2');

const conn = new Client();
conn.on('ready', () => {
    console.log('SSH connection ready');
    conn.exec('cat ~/.config/syncthing/config.xml || cat ~/syncthing_config/config.xml', (err, stream) => {
        if (err) {
            console.error('Exec error:', err);
            conn.end();
            return;
        }
        let output = '';
        stream.on('close', (code, signal) => {
            console.log('--- PHONE CONFIG DEVICE SECTIONS ---');
            // Extract all device nodes
            const devRegex = /<device id="([^"]+)" name="([^"]+)"/g;
            let match;
            while ((match = devRegex.exec(output)) !== null) {
                console.log(`Device ID: ${match[1]}, Name: ${match[2]}`);
            }
            conn.end();
        }).on('data', (data) => {
            output += data.toString();
        }).stderr.on('data', (data) => {
            process.stderr.write(data.toString());
        });
    });
}).on('error', (err) => {
    console.error('SSH Error:', err.message);
}).connect({
    host: '192.168.1.2',
    port: 8022,
    username: 'u0_a',
    password: '123'
});
