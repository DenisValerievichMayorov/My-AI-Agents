const fs = require('fs');
const path = require('path');
const os = require('os');

function findConfigXml(dir) {
    try {
        const files = fs.readdirSync(dir);
        for (const file of files) {
            const fullPath = path.join(dir, file);
            if (file === 'config.xml' && fullPath.includes('syncthing')) {
                return fullPath;
            }
            const stat = fs.statSync(fullPath);
            if (stat.isDirectory() && !file.startsWith('.') && file !== 'node_modules') {
                const found = findConfigXml(fullPath);
                if (found) return found;
            }
        }
    } catch (e) {}
    return null;
}

// Check common locations directly first
const commonLocations = [
    path.join(os.homedir(), '.config/syncthing/config.xml'),
    path.join(os.homedir(), '.local/state/syncthing/config.xml'),
    path.join(os.homedir(), 'Library/Application Support/Syncthing/config.xml'),
];

let foundPath = null;
for (const loc of commonLocations) {
    if (fs.existsSync(loc)) {
        foundPath = loc;
        break;
    }
}

if (!foundPath) {
    foundPath = findConfigXml(os.homedir());
}

if (foundPath) {
    console.log(`Found config.xml at: ${foundPath}`);
    const xml = fs.readFileSync(foundPath, 'utf8');
    const folderRegex = /<folder id="([^"]+)" label="([^"]+)" path="([^"]+)"/g;
    let match;
    console.log("Configured Syncthing folders on phone:");
    while ((match = folderRegex.exec(xml)) !== null) {
        console.log(`- Folder ID: ${match[1]}, Label: ${match[2]}, Path: ${match[3]}`);
    }
} else {
    console.log("Syncthing config.xml not found anywhere on the phone's home directory!");
}
