const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();
conn.on('ready', () => {
    console.log('SSH connection ready');
    conn.sftp((err, sftp) => {
        if (err) {
            console.error('SFTP Init Error:', err);
            conn.end();
            return;
        }
        
        const remotePath = 'syncthing_config/config.xml';
        
        // Read file via SFTP
        sftp.readFile(remotePath, 'utf8', (errRead, data) => {
            if (errRead) {
                console.error('Error reading remote config:', errRead);
                conn.end();
                return;
            }
            
            console.log('Read config successfully. Replacing ID...');
            const oldId = 'RICIMP6-MYQN3EM-NNBCTHJ-IFVL5F7-UGJ3RTS-4JJRIE5-PBCRC65-STAYTQH';
            const newId = '37ZZ4JT-WQUBUHC-5KAJCG6-SIUFXSV-TR4PMQ6-O2L2K5O-2S5WMCA-5QRJGQU';
            
            if (!data.includes(oldId)) {
                console.log('Old ID not found in phone config.xml. Maybe already updated?');
                
                // Let's still make sure Syncthing is restarted
                const restartCmd = `
                    killall syncthing
                    sleep 2
                    nohup syncthing > ~/syncthing.log 2>&1 &
                    echo "Syncthing restarted on phone."
                `;
                conn.exec(restartCmd, (errRestart, streamRestart) => {
                    streamRestart.on('close', () => {
                        console.log('Syncthing restarted anyway.');
                        conn.end();
                    }).on('data', (d) => process.stdout.write(d.toString()));
                });
                return;
            }
            
            const updatedXml = data.split(oldId).join(newId);
            
            // Write file via SFTP
            sftp.writeFile(remotePath, updatedXml, 'utf8', (errWrite) => {
                if (errWrite) {
                    console.error('Error writing remote config:', errWrite);
                    conn.end();
                    return;
                }
                
                console.log('Phone config.xml updated successfully via SFTP!');
                
                // Restart Syncthing on the phone
                const restartCmd = `
                    killall syncthing
                    sleep 2
                    nohup syncthing > ~/syncthing.log 2>&1 &
                    echo "Syncthing restarted on phone."
                `;
                conn.exec(restartCmd, (errRestart, streamRestart) => {
                    streamRestart.on('close', () => {
                        console.log('Syncthing restarted on phone successfully!');
                        conn.end();
                    }).on('data', (d) => process.stdout.write(d.toString()));
                });
            });
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
