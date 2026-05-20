const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const configPath = '/data/data/com.termux/files/home/syncthing_config/config.xml';
if (fs.existsSync(configPath)) {
    let xml = fs.readFileSync(configPath, 'utf8');
    
    // We want to replace the folder id="twwct-lkqgn" block with folder id="default"
    const targetFolderStart = xml.indexOf('<folder id="twwct-lkqgn"');
    if (targetFolderStart !== -1) {
        const targetFolderEnd = xml.indexOf('</folder>', targetFolderStart) + '</folder>'.length;
        
        const newFolderBlock = `    <folder id="default" label="Default Folder" path="/data/data/com.termux/files/home/Sync" type="sendreceive" rescanIntervalS="3600" fsWatcherEnabled="true" fsWatcherDelayS="10" ignorePerms="false" autoNormalize="true">
        <filesystemType>basic</filesystemType>
        <device id="KFY2NMX-IU3IHRB-GBGTCWP-AHGR6DJ-Z6W6ID3-QLAGBUG-NOHT36L-2BXN2QP" introducedBy="">
            <encryptionPassword></encryptionPassword>
        </device>
        <device id="RICIMP6-MYQN3EM-NNBCTHJ-IFVL5F7-UGJ3RTS-4JJRIE5-PBCRC65-STAYTQH" introducedBy="">
            <encryptionPassword></encryptionPassword>
        </device>
        <device id="THMOXLH-TJILN4C-FSLKHIV-QS2RUXS-GATGHGK-RH2JM5B-CE5VVKO-DLT35QZ" introducedBy="">
            <encryptionPassword></encryptionPassword>
        </device>
        <minDiskFree unit="%">1</minDiskFree>
        <versioning>
            <cleanupIntervalS>3600</cleanupIntervalS>
            <fsPath></fsPath>
            <fsType>basic</fsType>
        </versioning>
        <copiers>0</copiers>
        <pullerMaxPendingKiB>0</pullerMaxPendingKiB>
        <hashers>0</hashers>
        <order>random</order>
        <ignoreDelete>false</ignoreDelete>
        <scanProgressIntervalS>0</scanProgressIntervalS>
        <pullerPauseS>0</pullerPauseS>
        <maxConflicts>10</maxConflicts>
        <disableSparseFiles>false</disableSparseFiles>
        <disableTempIndexes>false</disableTempIndexes>
        <paused>false</paused>
        <weakHashThresholdPct>25</weakHashThresholdPct>
        <markerName>.stfolder</markerName>
        <copyOwnershipFromParent>false</copyOwnershipFromParent>
        <modTimeWindowS>0</modTimeWindowS>
        <maxConcurrentWrites>16</maxConcurrentWrites>
        <disableFsync>false</disableFsync>
        <blockPullOrder>standard</blockPullOrder>
        <copyRangeMethod>standard</copyRangeMethod>
        <caseSensitiveFS>false</caseSensitiveFS>
        <junctionsAsDirs>false</junctionsAsDirs>
    </folder>`;

        xml = xml.substring(0, targetFolderStart) + newFolderBlock + xml.substring(targetFolderEnd);
        fs.writeFileSync(configPath, xml, 'utf8');
        console.log("Successfully replaced twwct-lkqgn folder with shared 'default' folder in Termux syncthing config!");
        
        // Let's restart syncthing
        try {
            console.log("Restarting syncthing on phone...");
            // Querying Syncthing port 8384 API to restart it gracefully (recommended over kill)
            // But since curl command might have a different API key on the phone, let's just kill and it will auto-restart if it's running via daemon, or we can restart it.
            // Let's check the API key on the phone:
            const apiKeyMatch = xml.match(/<apikey>([^<]+)<\/apikey>/);
            if (apiKeyMatch) {
                const apiKey = apiKeyMatch[1];
                console.log(`Using API key: ${apiKey}`);
                execSync(`curl -s -X POST -H "X-API-Key: ${apiKey}" http://127.0.0.1:8384/rest/system/restart`);
                console.log("Graceful restart sent successfully via REST API!");
            } else {
                console.log("API key not found, using kill...");
                execSync("pkill -x syncthing");
                console.log("Killed syncthing, it should restart.");
            }
        } catch (e) {
            console.log("Error restarting syncthing: " + e.message);
        }
    } else {
        console.log("twwct-lkqgn folder not found in config.xml, maybe already fixed?");
    }
} else {
    console.log("Config not found!");
}
