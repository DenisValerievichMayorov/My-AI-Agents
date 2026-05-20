const fs = require('fs');
const path = require('path');
const os = require('os');

const bashrcPath = path.join(os.homedir(), '.bashrc');
if (fs.existsSync(bashrcPath)) {
    let content = fs.readFileSync(bashrcPath, 'utf8');
    const oldLine = 'export OLLAMA_HOST=127.0.0.1:11434';
    const newLine = 'export OLLAMA_HOST=http://100.72.214.118:11434';
    
    if (content.includes(oldLine)) {
        content = content.replace(oldLine, newLine);
        fs.writeFileSync(bashrcPath, content, 'utf8');
        console.log('Successfully updated OLLAMA_HOST in ~/.bashrc to Tailscale IP!');
    } else if (content.includes(newLine)) {
        console.log('OLLAMA_HOST is already pointing to Tailscale IP in ~/.bashrc.');
    } else {
        fs.appendFileSync(bashrcPath, `\n# GMC Ollama config (PC over Tailscale)\n${newLine}\n`, 'utf8');
        console.log('Appended OLLAMA_HOST pointing to Tailscale IP in ~/.bashrc.');
    }
} else {
    console.log('~/.bashrc not found!');
}
