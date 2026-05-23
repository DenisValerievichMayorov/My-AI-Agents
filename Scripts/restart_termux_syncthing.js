const { Client } = require('ssh2');

const conn = new Client();
const cmd = `
echo "=== Restarting Syncthing on Termux ==="
killall syncthing
sleep 2
nohup syncthing > ~/syncthing.log 2>&1 &
echo "Syncthing restarted."
`;

conn.on('ready', () => {
    conn.exec(cmd, (err, stream) => {
        if (err) throw err;
        stream.on('close', (code, signal) => {
            conn.end();
        }).on('data', (data) => {
            process.stdout.write(data.toString());
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
