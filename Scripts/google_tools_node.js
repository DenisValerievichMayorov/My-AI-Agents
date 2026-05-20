const fs = require('fs');
const path = require('path');
const https = require('https');

const SYNC_DIR = __dirname;
const TOKEN_PATH = path.join(SYNC_DIR, 'google_token.json');

function request(url, options = {}, postData = null) {
    return new Promise((resolve, reject) => {
        const req = https.request(url, options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                if (res.statusCode >= 200 && res.statusCode < 300) {
                    try {
                        resolve(JSON.parse(data));
                    } catch (e) {
                        resolve(data);
                    }
                } else {
                    reject(new Error(`Status ${res.statusCode}: ${data}`));
                }
            });
        });
        req.on('error', reject);
        if (postData) {
            req.write(postData);
        }
        req.end();
    });
}

async function getAccessToken() {
    if (!fs.existsSync(TOKEN_PATH)) {
        throw new Error("Token file not found!");
    }
    const tokenData = JSON.parse(fs.readFileSync(TOKEN_PATH, 'utf8'));
    const now = new Date();
    const expiry = new Date(tokenData.expiry);

    if (now >= new Date(expiry.getTime() - 5 * 60 * 1000)) {
        const params = new URLSearchParams({
            client_id: tokenData.client_id,
            client_secret: tokenData.client_secret,
            refresh_token: tokenData.refresh_token,
            grant_type: 'refresh_token'
        });

        const res = await request(tokenData.token_uri, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        }, params.toString());

        tokenData.token = res.access_token;
        if (res.expires_in) {
            tokenData.expiry = new Date(Date.now() + res.expires_in * 1000).toISOString();
        }
        fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokenData, null, 2), 'utf8');
    }
    return tokenData.token;
}

// 1. Google Drive List
async function listDrive() {
    try {
        const token = await getAccessToken();
        const headers = { 'Authorization': `Bearer ${token}` };
        const res = await request('https://www.googleapis.com/drive/v3/files?pageSize=5&fields=files(id,name,mimeType)', { headers });
        const files = res.files || [];
        if (files.length === 0) return "Файлы в Drive не найдены.";

        let out = "Последние файлы в Google Drive:\n";
        for (const file of files) {
            out += `- ${file.name} (${file.mimeType})\n`;
        }
        return out;
    } catch (e) {
        return `Ошибка Drive: ${e.message}`;
    }
}

// 2. Google Photos List
async function listPhotos() {
    try {
        const token = await getAccessToken();
        const headers = { 'Authorization': `Bearer ${token}` };
        const res = await request('https://photoslibrary.googleapis.com/v1/mediaItems?pageSize=5', { headers });
        const items = res.mediaItems || [];
        if (items.length === 0) return "Фото (созданные этим приложением) не найдены. Обратите внимание: с 31 марта 2025 года Google отключил общий доступ к полной библиотеке Photos через API.";

        let out = "Последние фото в Google Photos (созданные этим приложением):\n";
        for (const item of items) {
            out += `- ${item.filename} (${item.mimeType})\n`;
        }
        return out;
    } catch (e) {
        if (e.message.includes('403')) {
            return `Ошибка Фото: Доступ ограничен (403). Обратите внимание: с 31 марта 2025 года Google полностью удалил область видимости 'photoslibrary.readonly' из соображений безопасности. Теперь разрешен доступ только к фото, созданным этим приложением через область 'photoslibrary.readonly.appcreateddata'. Рекомендуется заново авторизоваться через google_auth.py.`;
        }
        return `Ошибка Фото: ${e.message}`;
    }
}

// 3. Google Calendar List
async function listCalendar() {
    try {
        const token = await getAccessToken();
        const headers = { 'Authorization': `Bearer ${token}` };
        const now = new Date().toISOString();
        const res = await request(`https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin=${encodeURIComponent(now)}&maxResults=5&singleEvents=true&orderBy=startTime`, { headers });
        const events = res.items || [];
        if (events.length === 0) return "Ближайших событий не найдено.";

        let out = "Ваши ближайшие события:\n";
        for (const event of events) {
            const start = event.start.dateTime || event.start.date;
            out += `- ${start}: ${event.summary}\n`;
        }
        return out;
    } catch (e) {
        return `Ошибка Календаря: ${e.message}`;
    }
}

// 4. Google Gmail Search
async function searchGmail(query) {
    try {
        const token = await getAccessToken();
        const headers = { 'Authorization': `Bearer ${token}` };
        const listRes = await request(`https://gmail.googleapis.com/gmail/v1/users/me/messages?q=${encodeURIComponent(query)}&maxResults=3`, { headers });
        const messages = listRes.messages || [];
        if (messages.length === 0) return `По запросу '${query}' ничего не найдено.`;

        let out = `Результаты поиска в Gmail по '${query}':\n`;
        for (const m of messages) {
            const msg = await request(`https://gmail.googleapis.com/gmail/v1/users/me/messages/${m.id}`, { headers });
            const headersList = msg.payload.headers || [];
            const subject = (headersList.find(h => h.name === 'Subject') || { value: 'No Subject' }).value;
            const from = (headersList.find(h => h.name === 'From') || { value: 'Unknown Sender' }).value;
            const date = (headersList.find(h => h.name === 'Date') || { value: 'Unknown Date' }).value;
            out += `- [${date}] From: ${from}\n  Subject: ${subject}\n  Snippet: ${msg.snippet}\n`;
        }
        return out;
    } catch (e) {
        return `Ошибка Gmail: ${e.message}`;
    }
}

// 5. Google Gmail Create Draft
async function createGmailDraft(subject, to, body) {
    try {
        const token = await getAccessToken();
        // Construct basic MIME email
        const emailContent = `To: ${to}\r\nSubject: ${subject}\r\n\r\n${body}`;
        const base64Safe = Buffer.from(emailContent)
            .toString('base64')
            .replace(/\+/g, '-')
            .replace(/\//g, '_')
            .replace(/=+$/, '');

        const postBody = JSON.stringify({
            message: {
                raw: base64Safe
            }
        });

        const draft = await request('https://gmail.googleapis.com/gmail/v1/users/me/drafts', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        }, postBody);

        return `✅ Черновик письма успешно создан в Gmail! ID черновика: ${draft.id}`;
    } catch (e) {
        return saveLocalDraft(subject, to, body, e.message);
    }
}

function saveLocalDraft(subject, to, body, reason) {
    const draftFile = path.join(SYNC_DIR, "prepared_drafts.txt");
    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
    fs.appendFileSync(draftFile, `\n--- Черновик от ${timestamp} ---\nКому: {to}\nТема: {subject}\n\n{body}\n----------------------\n`, 'utf8');
    return `⚠️ Резервный режим (${reason}): Черновик успешно подготовлен локально в prepared_drafts.txt и синхронизирован через Syncthing!`;
}

// 6. Google Tasks List
async function listTasks() {
    try {
        const token = await getAccessToken();
        const headers = { 'Authorization': `Bearer ${token}` };

        const listsRes = await request('https://tasks.googleapis.com/tasks/v1/users/@me/lists?maxResults=10', { headers });
        const items = listsRes.items || [];
        if (items.length === 0) return "Списков задач не найдено.";

        let out = "📋 Ваши списки задач Google Tasks:\n";
        for (const item of items) {
            out += `- ${item.title} (ID: ${item.id})\n`;
        }
        out += "\n📌 Активные задачи в основном списке:\n";

        const tasksRes = await request('https://tasks.googleapis.com/tasks/v1/lists/@default/tasks?maxResults=20&showCompleted=false', { headers });
        const tasks = tasksRes.items || [];
        if (tasks.length === 0) {
            out += "  (Нет активных задач)\n";
        } else {
            for (const task of tasks) {
                if (task.title) {
                    const notes = task.notes ? ` — ${task.notes}` : "";
                    out += `  [ ] ${task.title}${notes}\n`;
                }
            }
        }
        return out;
    } catch (e) {
        return `Ошибка Tasks: ${e.message}`;
    }
}

// 7. Google Tasks Create
async function addTask(title, notes = null) {
    try {
        const token = await getAccessToken();
        const body = JSON.stringify({ title, notes });
        const result = await request('https://tasks.googleapis.com/tasks/v1/lists/@default/tasks', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        }, body);
        return `✅ Задача '${title}' успешно добавлена в Google Tasks! ID: ${result.id}`;
    } catch (e) {
        return saveLocalTask(title, notes, e.message);
    }
}

function saveLocalTask(title, notes, reason) {
    const tasksFile = path.join(SYNC_DIR, "prepared_tasks.txt");
    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
    fs.appendFileSync(tasksFile, `- [ ] ${title} (${notes || ''}) [Подготовлено: ${timestamp}] [Ошибка: ${reason}]\n`, 'utf8');
    return `⚠️ Резервный режим (${reason}): Задача записана в prepared_tasks.txt и синхронизирована через Syncthing!`;
}

// 8. Google Drive Download
async function downloadDriveFile(filename, destPath = null) {
    try {
        const token = await getAccessToken();
        const headers = { 'Authorization': `Bearer ${token}` };

        // Search for file ID by name
        const searchRes = await request(`https://www.googleapis.com/drive/v3/files?q=name='${encodeURIComponent(filename)}'&fields=files(id,name,mimeType)`, { headers });
        const files = searchRes.files || [];
        if (files.length === 0) return `Ошибка: Файл '${filename}' не найден в Google Drive.`;

        const file = files[0];
        const fileId = file.id;
        const outPath = destPath || path.join(SYNC_DIR, filename);

        // Download file content stream
        return new Promise((resolve, reject) => {
            const options = {
                headers: { 'Authorization': `Bearer ${token}` }
            };
            const req = https.get(`https://www.googleapis.com/drive/v3/files/${fileId}?alt=media`, options, (res) => {
                if (res.statusCode !== 200) {
                    let errData = '';
                    res.on('data', chunk => errData += chunk);
                    res.on('end', () => reject(new Error(`Status ${res.statusCode}: ${errData}`)));
                    return;
                }
                const fileStream = fs.createWriteStream(outPath);
                res.pipe(fileStream);
                fileStream.on('finish', () => {
                    fileStream.close();
                    resolve(`✅ Файл '${filename}' успешно скачан в ${outPath}!`);
                });
                fileStream.on('error', (err) => {
                    fs.unlink(outPath, () => {});
                    reject(err);
                });
            });
            req.on('error', reject);
        });
    } catch (e) {
        return `Ошибка скачивания с Drive: ${e.message}`;
    }
}

async function main() {
    const args = process.argv.slice(2);
    const cmd = args[0];

    let output = "";
    if (cmd === 'drive') {
        output = await listDrive();
    } else if (cmd === 'photos') {
        output = await listPhotos();
    } else if (cmd === 'calendar') {
        output = await listCalendar();
    } else if (cmd === 'gmail' && args[1]) {
        output = await searchGmail(args[1]);
    } else if (cmd === 'draft' && args[1] && args[2] && args[3]) {
        output = await createGmailDraft(args[1], args[2], args[3]);
    } else if (cmd === 'tasks') {
        output = await listTasks();
    } else if (cmd === 'task' && args[1]) {
        output = await addTask(args[1], args[2] || null);
    } else if (cmd === 'download' && args[1]) {
        output = await downloadDriveFile(args[1], args[2] || null);
    } else {
        output = "Использование: node google_tools_node.js [drive|photos|calendar|gmail|draft|tasks|task|download]";
    }
    console.log(output);
}

main();
