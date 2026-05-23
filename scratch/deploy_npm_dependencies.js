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
    console.log('✅ SSH Ready!');
    conn.sftp((err, sftp) => {
        if (err) throw err;
        
        const localPkg = path.join('C:', 'Users', 'anton', 'Sync', 'package.json');
        const remotePkg = 'Sync/package.json';
        
        console.log('Deploying package.json to phone...');
        sftp.fastPut(localPkg, remotePkg, (errPut) => {
            if (errPut) {
                console.error('Error uploading package.json:', errPut);
                conn.end();
                return;
            }
            
            console.log('package.json uploaded successfully! Running npm install on phone...');
            
            conn.exec('cd ~/Sync && npm install --no-audit --no-fund', (errExec, stream) => {
                if (errExec) throw errExec;
                
                stream.on('close', (code) => {
                    console.log(`npm install finished with code ${code}`);
                    conn.end();
                }).on('data', (data) => {
                    process.stdout.write(data.toString());
                }).stderr.on('data', (data) => {
                    process.stderr.write(data.toString());
                });
            });
        });
    });
}).on('error', (err) => {
    console.error('Connection error:', err);
}).connect(config);
