const { Client } = require('ssh2');

const conn = new Client();
const cmd = `
echo "=== Checking rclone process ==="
ps aux | grep rclone
echo "=== Deleting lock file ==="
rclone deletefile "/data/data/com.termux/files/home/.cache/rclone/bisync/data_data_com.termux_files_home_Sync..GoogleDrive_Sync.lck" || true
echo "=== Running Rclone Sync Manually ==="
bash ~/rclone_sync.sh
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
