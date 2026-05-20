const fs = require('fs');
const path = require('path');
const os = require('os');

const bashrcPath = path.join(os.homedir(), '.bashrc');
try {
    if (fs.existsSync(bashrcPath)) {
        console.log(fs.readFileSync(bashrcPath, 'utf8'));
    } else {
        console.log(".bashrc not found!");
    }
} catch (e) {
    console.log("Error reading .bashrc: " + e.message);
}
