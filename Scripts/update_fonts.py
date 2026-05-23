import re

path = r'C:\Users\anton\Sync\Scripts\agent_listener.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update DASHBOARD_HTML header to include A- A+ buttons
header_search = r'<div class="terminal-header">\s*<span class="terminal-title" style="color: var\(--accent-purple\);">\s*<svg.*?</svg>\s*Чат GMC \(live \+ syncthing\)\s*</span>\s*</div>'
header_replace = """<div class="terminal-header">
                <span class="terminal-title" style="color: var(--accent-purple);">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                    Чат GMC (live + syncthing)
                </span>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 14px; border-radius: 6px; width: auto; height: auto;" onclick="changeFontSize(-1)">A-</button>
                    <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 14px; border-radius: 6px; width: auto; height: auto;" onclick="changeFontSize(1)">A+</button>
                </div>
            </div>"""
text = re.sub(header_search, header_replace, text, count=1)

# 2. Update DASHBOARD_HTML JS
script_search = r'(<script>\s*function updateTime\(\) {)'
script_replace = """<script>
        function changeFontSize(step) {
            let currentSize = parseFloat(localStorage.getItem('chatFontSize')) || 16.5;
            currentSize += step;
            if (currentSize < 10) currentSize = 10;
            if (currentSize > 30) currentSize = 30;
            localStorage.setItem('chatFontSize', currentSize);
            applyFontSize(currentSize);
        }
        function applyFontSize(size) {
            const chatScreen = document.getElementById('chat-screen');
            const cmdInput = document.getElementById('cmd-input');
            if (chatScreen) chatScreen.style.fontSize = size + 'px';
            if (cmdInput) cmdInput.style.fontSize = size + 'px';
        }
        document.addEventListener('DOMContentLoaded', () => {
            const savedSize = localStorage.getItem('chatFontSize');
            if (savedSize) applyFontSize(parseFloat(savedSize));
        });

        function updateTime() {"""
text = re.sub(script_search, script_replace, text, count=1)

# 3. Update COMBINED_HTML buttons
comb_header_search = r'(<div style="display:flex;gap:12px;">\s*)(<input type="text" id="cmd-input")'
comb_header_replace = r'\1<button onclick="changeFontSize(-1)" style="padding:12px;border-radius:8px;border:1px solid var(--border-color);background:rgba(156,163,175,0.08);color:#d1d5db;cursor:pointer;font-weight:bold;">A-</button>\n                    <button onclick="changeFontSize(1)" style="padding:12px;border-radius:8px;border:1px solid var(--border-color);background:rgba(156,163,175,0.08);color:#d1d5db;cursor:pointer;font-weight:bold;">A+</button>\n                    \2'
text = re.sub(comb_header_search, comb_header_replace, text, count=1)

# 4. Update COMBINED_HTML JS
comb_script_search = r'(<script>\s*let showDone = false;)'
comb_script_replace = """<script>
        function changeFontSize(step) {
            let currentSize = parseFloat(localStorage.getItem('chatFontSize')) || 15;
            currentSize += step;
            if (currentSize < 10) currentSize = 10;
            if (currentSize > 30) currentSize = 30;
            localStorage.setItem('chatFontSize', currentSize);
            applyFontSize(currentSize);
        }
        function applyFontSize(size) {
            const chatScreen = document.getElementById('chat-screen');
            const cmdInput = document.getElementById('cmd-input');
            if (chatScreen) chatScreen.style.fontSize = size + 'px';
            if (cmdInput) cmdInput.style.fontSize = size + 'px';
        }
        document.addEventListener('DOMContentLoaded', () => {
            const savedSize = localStorage.getItem('chatFontSize');
            if (savedSize) applyFontSize(parseFloat(savedSize));
        });

        let showDone = false;"""
text = re.sub(comb_script_search, comb_script_replace, text, count=1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Done updating agent_listener.py')
