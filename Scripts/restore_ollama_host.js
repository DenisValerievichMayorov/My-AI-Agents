const fs = require('fs');
const path = require('path');
const os = require('os');

const bashrcPath = path.join(os.homedir(), '.bashrc');
if (fs.existsSync(bashrcPath)) {
    let content = fs.readFileSync(bashrcPath, 'utf8');
    const oldLine = 'export OLLAMA_HOST=http://100.72.214.118:11434';
    const newLine = 'export OLLAMA_HOST=127.0.0.1:11434';
    
    if (content.includes(oldLine)) {
        content = content.replace(oldLine, newLine);
        fs.writeFileSync(bashrcPath, content, 'utf8');
        console.log('Successfully restored OLLAMA_HOST in ~/.bashrc to 127.0.0.1:11434!');
    } else {
        console.log('No Tailscale IP OLLAMA_HOST found in ~/.bashrc to restore.');
    }
} else {
    console.log('~/.bashrc not found!');
}
