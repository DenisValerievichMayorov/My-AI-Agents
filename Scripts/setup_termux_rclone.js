const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const rcloneConfig = `[GoogleDrive]
type = drive
scope = drive
token = {"access_token":"ya29.a0AQvPyIOAUO_Wi7iQrU4a1vpALw5z5NmKSKT1hh303CAtjO8hE-kzInvdzd4-qCuwRDJDxEyu5rbb2cM87ODfvIEpyEmwcVIPkpTY3jXkP7dd2OYY17IO5jM1BxSX-HkPBI8L8JkTO8YMhgpo4fykM8zH6ERrzM6wITIuXexUkgktEn8sb1cmiYF6UyLGKyIxtyLZSDgaCgYKAZMSARESFQHGX2Mi_KW9lP8JmTsCLwBL9jPZMA0206","token_type":"Bearer","refresh_token":"1//037ONybIh0NjFCgYIARAAGAMSNwF-L9Irhf-CILQmmriEBPl8TeVteBBgHMpXns3AMEeUcANEbLC6o6i8pVbVGq1Ddwigrs7mRic","expiry":"2026-05-22T18:21:52.8230525+02:00","expires_in":3599}
`;

const script = `
pkg update -y
pkg install rclone cronie -y
mkdir -p ~/.config/rclone
cat << 'EOF' > ~/.config/rclone/rclone.conf
${rcloneConfig}
EOF
echo "rclone.conf created."

mkdir -p ~/Sync
cat << 'EOF' > ~/rclone_sync.sh
#!/data/data/com.termux/files/usr/bin/bash
if [ ! -f ~/.rclone_bisync_init.flag ]; then
    rclone bisync ~/Sync GoogleDrive:Sync --resync --create-empty-src-dirs --force --verbose
    if [ $? -eq 0 ]; then
        touch ~/.rclone_bisync_init.flag
    fi
else
    rclone bisync ~/Sync GoogleDrive:Sync --create-empty-src-dirs --force --verbose
fi
EOF
chmod +x ~/rclone_sync.sh

# Termux doesn't run crond by default easily on boot, 
# but termux-job-scheduler is built-in and better for Android.
pkg install termux-api -y
termux-job-scheduler -s ~/rclone_sync.sh --period-ms 900000 --persisted true
echo "Setup complete on Termux!"
`;

conn.on('ready', () => {
    console.log('SSH Connection Ready! Sending commands to Termux...');
    conn.exec(script, (err, stream) => {
        if (err) throw err;
        stream.on('close', (code, signal) => {
            console.log('SSH closed.');
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
