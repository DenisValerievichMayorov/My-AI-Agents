const fs = require('fs');
const { OAuth2Client } = require('google-auth-library');
const express = require('express');
const { exec } = require('child_process');

const KEYS_FILE = 'C:\\Users\\anton\\Sync\\client_secret.json';
const TOKEN_FILE = 'C:\\Users\\anton\\Sync\\speech_token.json';
const SCOPES = ['https://www.googleapis.com/auth/cloud-platform'];
const PORT = 3000;

async function main() {
    console.log('Loading client secrets...');
    const keys = JSON.parse(fs.readFileSync(KEYS_FILE, 'utf8')).installed;
    const oAuth2Client = new OAuth2Client(
        keys.client_id,
        keys.client_secret,
        `http://localhost:${PORT}`
    );

    // Check if we already have a valid token
    if (fs.existsSync(TOKEN_FILE)) {
        try {
            const token = JSON.parse(fs.readFileSync(TOKEN_FILE, 'utf8'));
            oAuth2Client.setCredentials(token);
            console.log('Existing token loaded. Checking validity...');
            // Try to refresh or get access token
            await oAuth2Client.getAccessToken();
            console.log('Token is valid. Google Cloud Speech setup complete!');
            return;
        } catch (e) {
            console.log('Token is invalid or expired. We need to re-authenticate.');
        }
    }

    const authorizeUrl = oAuth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: SCOPES,
        prompt: 'consent'
    });

    const app = express();
    let server;

    app.get('/', async (req, res) => {
        if (req.query.code) {
            try {
                const { tokens } = await oAuth2Client.getToken(req.query.code);
                oAuth2Client.setCredentials(tokens);
                fs.writeFileSync(TOKEN_FILE, JSON.stringify(tokens, null, 2));
                console.log(`Token saved to ${TOKEN_FILE}`);
                res.send('<h1>Authentication successful!</h1><p>You can close this tab and return to Antigravity.</p>');
                setTimeout(() => {
                    server.close();
                    process.exit(0);
                }, 1000);
            } catch (err) {
                res.send('<h1>Error occurred</h1><p>' + err.message + '</p>');
            }
        } else {
            res.send('<h1>No code provided in query</h1>');
        }
    });

    server = app.listen(PORT, () => {
        console.log(`Listening on http://localhost:${PORT}`);
        console.log('Opening browser for authorization...');
        
        // Open the browser automatically
        const cmd = process.platform === 'win32' ? `start "" "${authorizeUrl}"` : `open "${authorizeUrl}"`;
        exec(cmd, (err) => {
            if (err) console.error('Failed to open browser automatically. Please click this link:', authorizeUrl);
        });
    });
}

main().catch(console.error);
