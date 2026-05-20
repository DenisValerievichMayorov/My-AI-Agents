const fs = require('fs');
const path = require('path');

const configPath = '/data/data/com.termux/files/home/syncthing_config/config.xml';
if (fs.existsSync(configPath)) {
    const xml = fs.readFileSync(configPath, 'utf8');
    // Let's print all folder configurations including their shared devices
    const folderRegex = /<folder id="([^"]+)"[\s\S]*?<\/folder>/g;
    let match;
    console.log("--- PHONE FOLDER DETAILS ---");
    while ((match = folderRegex.exec(xml)) !== null) {
        const folderXml = match[0];
        const folderId = match[1];
        const pathMatch = folderXml.match(/path="([^"]+)"/);
        const labelMatch = folderXml.match(/label="([^"]+)"/);
        const devices = [...folderXml.matchAll(/<device id="([^"]+)"/g)].map(m => m[1]);
        
        console.log(`Folder ID: ${folderId}`);
        console.log(`  Label: ${labelMatch ? labelMatch[1] : 'N/A'}`);
        console.log(`  Path: ${pathMatch ? pathMatch[1] : 'N/A'}`);
        console.log(`  Shared with devices:`);
        devices.forEach(d => console.log(`    - ${d}`));
    }
} else {
    console.log("Config not found!");
}
