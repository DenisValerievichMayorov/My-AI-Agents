const puppeteer = require('puppeteer-core');
(async () => {
    try {
        const browser = await puppeteer.launch({
            executablePath: '/data/data/com.termux/files/usr/bin/chromium-browser',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--disable-software-rasterizer',
                '--disable-extensions',
                '--single-process',
                '--user-data-dir=/data/data/com.termux/files/home/.chromium-test-profile'
            ]
        });
        const page = await browser.newPage();
        console.log('Navigating to google.com...');
        await page.goto('https://google.com', { waitUntil: 'networkidle2' });
        console.log('Title:', await page.title());
        await browser.close();
        console.log('Test successful!');
    } catch (e) {
        console.error('Test failed:', e);
    }
})();
