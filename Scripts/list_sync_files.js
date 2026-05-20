const fs = require('fs');
const path = require('path');
const os = require('os');

const syncDir = path.join(os.homedir(), 'Sync');
if (fs.existsSync(syncDir)) {
    const files = fs.readdirSync(syncDir);
    console.log(`Top-level files inside ~/Sync on phone (${files.length} items):`);
    files.slice(0, 15).forEach(f => console.log(`- ${f}`));
    if (files.length > 15) {
        console.log(`... and ${files.length - 15} more items`);
    }
} else {
    console.log("~/Sync directory not found!");
}
