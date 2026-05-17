import os
import shutil
import subprocess
import json
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import io
import pyautogui
import win32gui
import win32ui
import win32con
from ctypes import windll
from PIL import Image
import pyperclip
import time
import httpx

app = FastAPI()

# Configure logging
log_file = Path(__file__).with_name('logs.txt')
logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

# Thread pool for parallel task execution
executor = ThreadPoolExecutor(max_workers=3)

class TaskRequest(BaseModel):
    task: str

class ClickRequest(BaseModel):
    x: float
    y: float

def execute_task(task: str) -> dict:
    logging.info(f"Executing task via CLI: {task}")
    hwnd = find_antigravity_hwnd()
    if not hwnd:
        msg = "ERROR: Antigravity window not found!"
        logging.error(f"Task failed. Result: {{\"error\": \"{msg}\"}}")
        return {"error": msg}

    try:
        # Give focus to the window
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass # Sometimes SetForegroundWindow throws exception if process doesn't have permission
        time.sleep(0.5)

        # Copy to clipboard and paste safely
        pyperclip.copy(task)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)

        # Press Enter
        pyautogui.press('enter')

        res = {
            "stdout": f"Found window: {win32gui.GetWindowText(hwnd)}\\nWindow activated\\nTyped message: {task}\\nMessage sent!\\n",
            "stderr": "",
            "returncode": 0
        }
        logging.info(f"Task completed. Result: {json.dumps(res, ensure_ascii=False)}")
        return res
    except Exception as e:
        msg = str(e)
        logging.error(f"Task failed. Result: {json.dumps({'error': msg})}")
        return {"error": msg}

@app.get('/', response_class=HTMLResponse)
def get_ui():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Antigravity Orchestrator V2 (Control)</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            :root { --bg: #0f172a; --panel: #1e293b; --text: #f8fafc; --accent: #3b82f6; --accent-hover: #2563eb; --green: #10b981; --red: #ef4444; }
            body { 
                margin: 0; padding: 20px; font-family: 'Segoe UI', system-ui, sans-serif; 
                background: var(--bg); color: var(--text); 
                height: 100vh; box-sizing: border-box; display: flex; flex-direction: column; align-items: center;
            }
            .header { text-align: center; margin-bottom: 15px; }
            .header h1 { font-size: 1.5rem; margin: 0; background: linear-gradient(90deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .tabs { display: flex; gap: 4px; margin-bottom: 10px; width: 100%; max-width: 800px; }
            .tab-btn { flex: 1; padding: 10px; border: none; background: #334155; color: #94a3b8; border-radius: 8px 8px 0 0; cursor: pointer; font-weight: bold; transition: 0.2s; }
            .tab-btn.active { background: var(--panel); color: var(--text); }
            .tab-btn:hover { background: #475569; color: var(--text); }
            .panel { 
                width: 100%; max-width: 800px; display: none; flex-direction: column; gap: 12px; flex: 1;
                background: var(--panel); border-radius: 0 12px 12px 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.3);
            }
            .panel.active { display: flex; }
            textarea { 
                width: 100%; height: 100px; background: #0f172a; color: #f8fafc; 
                border: 1px solid #334155; border-radius: 8px; padding: 10px; box-sizing: border-box; resize: none; font-size: 1em;
            }
            textarea:focus { outline: none; border-color: var(--accent); }
            button { 
                background: var(--accent); color: white; border: none; padding: 10px 14px; border-radius: 8px; 
                font-weight: bold; cursor: pointer; transition: background 0.2s; font-size: 1em;
            }
            button:hover { background: var(--accent-hover); }
            button:disabled { opacity: 0.5; cursor: not-allowed; }
            .log-container { 
                flex: 1; background: #0f172a; border: 1px solid #334155; border-radius: 8px; 
                padding: 15px; overflow-y: auto; font-family: monospace; font-size: 0.9em; white-space: pre-wrap; word-wrap: break-word; 
            }
            .log-container a { color: #93c5fd; text-decoration: underline; }
            .log-container a:hover { color: #60a5fa; }
            .log-container a.file-link { color: #6ee7b7; }
            .log-container a.file-link:hover { color: #34d399; }
            .nav-link { margin-top: 8px; display: block; text-align: center; color: #93c5fd; text-decoration: none; font-weight: bold; font-size: 0.9em; }
            .nav-link:hover { text-decoration: underline; }

            .task-header { display: flex; gap: 8px; align-items: center; }
            .task-header input { flex: 1; padding: 8px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: white; font-size: 1em; }
            .task-header input:focus { outline: none; border-color: var(--accent); }
            .task-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; }
            .task-item { display: flex; align-items: center; gap: 8px; background: #0f172a; padding: 10px; border-radius: 8px; border: 1px solid #334155; }
            .task-item.done { opacity: 0.5; text-decoration: line-through; }
            .task-item .text { flex: 1; cursor: pointer; }
            .task-item .text.editing { display: none; }
            .task-item .edit-input { flex: 1; display: none; }
            .task-item .edit-input.show { display: block; }
            .btn-sm { padding: 4px 10px; font-size: 0.85em; border-radius: 6px; }
            .btn-green { background: var(--green); }
            .btn-green:hover { background: #059669; }
            .btn-red { background: var(--red); }
            .btn-red:hover { background: #dc2626; }
            .task-counter { font-size: 0.85em; color: #94a3b8; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Antigravity Control Panel</h1>
        </div>
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('logs')">📋 Logs</button>
            <button class="tab-btn" onclick="switchTab('tasks')">📌 Tasks</button>
        </div>
        <div class="panel active" id="panel-logs">
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <textarea id="task-input" placeholder="Enter task here to type..."></textarea>
                <div style="display: flex; gap: 10px;">
                    <button id="run-task" onclick="submitTask()" style="flex: 1;">Send Task (UI Type)</button>
                    <button id="run-gemini" onclick="submitGemini()" style="flex: 1; background: #10b981;">Ask Gemini CLI</button>
                </div>
                <div id="output" style="font-size: 0.9em; color: #94a3b8; min-height: 18px;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top:10px; margin-bottom: 5px;">
                <h3 style="margin: 0;">Server Logs (Newest First)</h3>
                <input type="text" id="log-search" placeholder="Search logs..." style="padding: 6px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: white; width: 200px;">
            </div>
            <div class="log-container" id="server-logs">Loading...</div>
        </div>
        <div class="panel" id="panel-tasks">
            <div class="task-header">
                <input type="text" id="new-task-input" placeholder="New task..." onkeydown="if(event.key==='Enter') addTask()">
                <button onclick="addTask()" class="btn-green">+ Add</button>
                <button onclick="toggleDone()" id="toggle-done-btn" class="btn-sm">Show done</button>
            </div>
            <div class="task-list" id="task-list"></div>
            <div class="task-counter" id="task-counter">0 active</div>
        </div>
        <div style="display: flex; gap: 10px; justify-content: center; margin-top: 8px; max-width: 800px;">
            <a href="/agent" class="nav-link">🤖 Agent Chat</a>
            <a href="/view" target="_blank" class="nav-link">📺 Screen Viewer</a>
            <a href="/" style="color:#94a3b8;" class="nav-link">🔄 Refresh</a>
        </div>
        
        <script>
            let currentTab = 'logs';
            let showDone = false;

            function switchTab(tab) {
                currentTab = tab;
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.textContent.includes(tab === 'logs' ? 'Logs' : 'Tasks')));
                document.querySelectorAll('.panel').forEach(p => p.classList.toggle('active', p.id === 'panel-' + tab));
                if (tab === 'tasks') loadTasks();
            }
            function linkify(text) {
                const urlRegex = /(https?:\/\/[^\s<]+)/g;
                const filePathRegex = /(?<![\/\w])([a-zA-Z]:\\(?:[^\\\s<"]+\\)*[^\\\s<":]*)/g;
                const fileUrlRegex = /(file:\/\/\/[^\s<]+)/g;
                
                let escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                
                escaped = escaped.replace(fileUrlRegex, function(match) {
                    return '<a href="' + match + '" class="file-link" target="_blank">' + match + '</a>';
                });
                
                escaped = escaped.replace(urlRegex, function(match) {
                    return '<a href="' + match + '" target="_blank" rel="noopener">' + match + '</a>';
                });
                
                escaped = escaped.replace(filePathRegex, function(match) {
                    return '<a href="file:///' + match.replace(/\\/g, '/') + '" class="file-link" target="_blank">' + match + '</a>';
                });
                
                return escaped;
            }

            async function updateLogs() {
                try {
                    const res = await fetch('/logs');
                    const data = await res.json();
                    const logElement = document.getElementById('server-logs');
                    const searchInput = document.getElementById('log-search').value.toLowerCase();
                    
                    let logsText = data.logs;
                    if (searchInput) {
                        const chunks = logsText.split('\\n\\n');
                        const filtered = chunks.filter(c => c.toLowerCase().includes(searchInput));
                        logsText = filtered.length > 0 ? filtered.join('\\n\\n') : 'No matching logs...';
                    }
                    
                    const isAtTop = logElement.scrollTop <= 10;
                    logElement.innerHTML = linkify(logsText);
                    if (isAtTop) {
                        logElement.scrollTop = 0;
                    }
                } catch(e) {}
            }
            setInterval(updateLogs, 2000);
            updateLogs();

            async function submitTask() {
                const btn = document.getElementById('run-task');
                const output = document.getElementById('output');
                const task = document.getElementById('task-input').value;
                if (!task.trim()) return;
                
                btn.disabled = true;
                output.innerText = "Running...";
                try {
                    const res = await fetch('/task', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({task})
                    });
                    const data = await res.json();
                    output.innerText = data.status === "success" ? "Success!" : "Failed";
                    document.getElementById('task-input').value = "";
                } catch(e) {
                    output.innerText = "Error: " + e;
                }
                btn.disabled = false;
            }

            async function submitGemini() {
                const btn = document.getElementById('run-gemini');
                const output = document.getElementById('output');
                const task = document.getElementById('task-input').value;
                if (!task.trim()) return;
                
                btn.disabled = true;
                output.innerText = "Running Gemini CLI...";
                try {
                    const res = await fetch('/gemini', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({task})
                    });
                    const data = await res.json();
                    output.innerText = data.status === "success" ? "Gemini Execution Success!" : "Gemini Failed";
                    document.getElementById('task-input').value = "";
                } catch(e) {
                    output.innerText = "Error: " + e;
                }
                btn.disabled = false;
            }

            // ─── Task Manager ─────────────────────────────────────
            async function loadTasks() {
                try {
                    const res = await fetch('/tasks');
                    const data = await res.json();
                    const list = document.getElementById('task-list');
                    const counter = document.getElementById('task-counter');
                    const tasks = showDone ? data.tasks : data.tasks.filter(t => !t.done);
                    const active = data.tasks.filter(t => !t.done).length;
                    counter.textContent = active + ' active / ' + data.tasks.length + ' total';
                    list.innerHTML = tasks.map(t => renderTask(t)).join('');
                } catch(e) {}
            }

            function renderTask(t) {
                const doneClass = t.done ? 'done' : '';
                const checked = t.done ? 'checked' : '';
                return '<div class="task-item ' + doneClass + '" data-id="' + t.id + '">' +
                    '<input type="checkbox" ' + checked + ' onchange="toggleTask(' + t.id + ', this.checked)">' +
                    '<span class="text" ondblclick="editTask(' + t.id + ')">' + escapeHtml(t.text) + '</span>' +
                    '<input class="edit-input" type="text" value="' + escapeHtml(t.text) + '" onblur="saveEdit(' + t.id + ', this)" onkeydown="if(event.key===\'Enter\') this.blur()">' +
                    '<button class="btn-sm btn-green" onclick="editTask(' + t.id + ')">✎</button>' +
                    '<button class="btn-sm btn-red" onclick="deleteTask(' + t.id + ')">✕</button>' +
                    '</div>';
            }

            function escapeHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

            async function addTask() {
                const input = document.getElementById('new-task-input');
                const text = input.value.trim();
                if (!text) return;
                await fetch('/tasks', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text})});
                input.value = '';
                loadTasks();
            }

            async function deleteTask(id) {
                await fetch('/tasks/' + id, {method:'DELETE'});
                loadTasks();
            }

            async function toggleTask(id, done) {
                await fetch('/tasks/' + id, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({done})});
                loadTasks();
            }

            function editTask(id) {
                const item = document.querySelector('.task-item[data-id="' + id + '"]');
                if (!item) return;
                item.querySelector('.text').classList.toggle('editing');
                const input = item.querySelector('.edit-input');
                input.classList.toggle('show');
                if (input.classList.contains('show')) input.focus();
            }

            async function saveEdit(id, el) {
                const text = el.value.trim();
                if (!text) { loadTasks(); return; }
                await fetch('/tasks/' + id, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text})});
                loadTasks();
            }

            function toggleDone() {
                showDone = !showDone;
                document.getElementById('toggle-done-btn').textContent = showDone ? 'Hide done' : 'Show done';
                loadTasks();
            }

            loadTasks();
        </script>
    </body>
    </html>
    """

@app.get('/view', response_class=HTMLResponse)
def get_view():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Antigravity Screen Viewer</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            :root { --bg: #0f172a; --panel: #1e293b; --text: #f8fafc; --accent: #3b82f6; --accent-hover: #2563eb; }
            body { 
                margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; 
                background: #000; color: var(--text); 
                height: 100vh; box-sizing: border-box; display: flex; flex-direction: column; 
            }
            .zoom-bar { 
                display: flex; gap: 10px; padding: 15px; align-items: center; background: var(--panel);
                border-bottom: 1px solid #334155; 
            }
            .screen-wrapper { 
                flex: 1; position: relative; background: #000; overflow: auto; 
            }
            #screen { 
                width: 100%; height: auto; object-fit: contain; cursor: crosshair; display: block; margin: 0 auto;
            }
            button { 
                background: var(--accent); color: white; border: none; padding: 8px 12px; border-radius: 6px; 
                font-weight: bold; cursor: pointer; transition: background 0.2s; 
            }
            button:hover { background: var(--accent-hover); }
        </style>
    </head>
    <body>
        <div class="zoom-bar">
            <h3 style="margin:0;">Live Screen Viewer</h3>
            <div style="flex:1;"></div>
            <button onclick="changeZoom(-25)">Zoom Out -</button>
            <button onclick="changeZoom(25)">Zoom In +</button>
            <button onclick="resetZoom()">Fit</button>
        </div>
        <div class="screen-wrapper">
            <img id="screen" src="/screen" alt="Live Screen Capture">
        </div>
        
        <script>
            let currentWidth = 100;
            function changeZoom(delta) {
                currentWidth = Math.max(25, currentWidth + delta);
                const img = document.getElementById("screen");
                img.style.width = currentWidth + "%";
                img.style.maxWidth = "none";
                img.style.objectFit = "fill";
            }
            function resetZoom() {
                currentWidth = 100;
                const img = document.getElementById("screen");
                img.style.width = "100%";
                img.style.maxWidth = "100%";
                img.style.objectFit = "contain";
            }

            setInterval(() => {
                document.getElementById("screen").src = "/screen?t=" + new Date().getTime();
            }, 1000);
            
            document.getElementById("screen").addEventListener("click", async function(e) {
                const x = e.offsetX / e.target.clientWidth;
                const y = e.offsetY / e.target.clientHeight;
                try {
                    await fetch('/click', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({x, y})
                    });
                } catch(e) { console.error("Click error", e); }
            });
        </script>
    </body>
    </html>
    """

class ReplyRequest(BaseModel):
    message: str

@app.post('/reply')
def post_reply(req: ReplyRequest):
    logging.info(f"ANTIGRAVITY_REPLY: {req.message}")
    return {"status": "reply_recorded"}

@app.get('/logs')
def get_logs():
    if not log_file.exists():
        return {"logs": "No logs yet."}
    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        
        formatted = []
        for line in lines:
            line = line.strip()
            # Extract timestamp (HH:MM:SS) if the line starts with standard logging format YYYY-MM-DD
            ts = ""
            if len(line) >= 20 and line[4] == '-' and line[7] == '-' and line[10] == ' ':
                ts = f"[{line[11:19]}] "
                
            if "Executing task via CLI: " in line:
                task = line.split("Executing task via CLI: ", 1)[-1]
                formatted.append(f"{ts}Task: {task}")
            elif "CLI not found, using UI automation for task: " in line:
                task = line.split("using UI automation for task: ", 1)[-1]
                formatted.append(f"{ts}Task: {task}")
            elif "Task completed. Result: " in line:
                result = line.split("Task completed. Result: ", 1)[-1]
                try:
                    res_json = json.loads(result)
                    if "stdout" in res_json and "Typed message:" in res_json["stdout"]:
                        msg = res_json["stdout"].split("Typed message: ")[1].split("\\n")[0]
                        formatted.append(f"{ts}[ORCHESTRATOR STATUS]: Successfully typed -> {msg}")
                    elif "error" in res_json:
                        formatted.append(f"{ts}[ORCHESTRATOR ERROR]: {res_json['error']}")
                except:
                    formatted.append(f"{ts}[ORCHESTRATOR RAW]: {result}")
            elif "ANTIGRAVITY_REPLY: " in line:
                reply = line.split("ANTIGRAVITY_REPLY: ", 1)[-1]
                formatted.append(f"\n{ts}[ANTIGRAVITY RESPONSE]:\n> {reply}")
            elif "Executing Gemini CLI: " in line:
                task = line.split("Executing Gemini CLI: ", 1)[-1]
                formatted.append(f"{ts}Gemini Query: {task}")
            elif "Gemini CLI completed. Result: " in line:
                result = line.split("Gemini CLI completed. Result: ", 1)[-1]
                try:
                    res_json = json.loads(result)
                    if "stdout" in res_json:
                        formatted.append(f"{ts}[GEMINI OUTPUT]:\n{res_json['stdout'].strip()}")
                    elif "error" in res_json:
                        formatted.append(f"{ts}[GEMINI ERROR]: {res_json['error']}")
                except:
                    formatted.append(f"{ts}[GEMINI RAW]: {result}")
            elif "Gemini CLI failed. Error: " in line:
                result = line.split("Gemini CLI failed. Error: ", 1)[-1]
                formatted.append(f"{ts}[GEMINI CRITICAL ERROR]: {result}")
                    
        return {"logs": "\n\n".join(formatted[-60:][::-1])}
    except Exception as e:
        return {"logs": f"Error reading logs: {e}"}

def find_antigravity_hwnd():
    candidates = []
    def callback(h, extra):
        if win32gui.IsWindowVisible(h):
            t = win32gui.GetWindowText(h).lower()
            if win32gui.GetClassName(h) == 'Chrome_WidgetWin_1':
                if ('antigravity' in t or 'cursor' in t) and 'chrome' not in t and 'orchestrator' not in t:
                    candidates.append((h, t))
    win32gui.EnumWindows(callback, None)
    
    for h, t in candidates:
        if 'antigravity' in t:
            return h
    for h, t in candidates:
        if 'cursor' in t:
            return h
    if candidates:
        return candidates[0][0]
    return None

def capture_window(hwnd):
    try:
        left, top, right, bot = win32gui.GetWindowRect(hwnd)
        w = right - left
        h = bot - top
        if w <= 0 or h <= 0: return None
        
        # Cannot use PrintWindow on hardware accelerated apps (turns black).
        # We crop the global screenshot instead.
        im = pyautogui.screenshot(region=(left, top, w, h))
        return im
    except Exception:
        return None

@app.get('/screen')
def get_screen():
    try:
        hwnd = find_antigravity_hwnd()
        if hwnd:
            im = capture_window(hwnd)
            if im:
                img_byte_arr = io.BytesIO()
                im.save(img_byte_arr, format='JPEG', quality=60)
                return Response(content=img_byte_arr.getvalue(), media_type="image/jpeg")
                
        # Fallback to fullscreen
        screenshot = pyautogui.screenshot()
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='JPEG', quality=60)
        return Response(content=img_byte_arr.getvalue(), media_type="image/jpeg")
    except Exception as e:
        return Response(content=b"", media_type="image/jpeg", status_code=500)

@app.post('/click')
def post_click(req: ClickRequest):
    try:
        hwnd = find_antigravity_hwnd()
        if hwnd:
            left, top, right, bot = win32gui.GetWindowRect(hwnd)
            w = right - left
            h = bot - top
            click_x = left + int(w * req.x)
            click_y = top + int(h * req.y)
            
            try:
                win32gui.SetForegroundWindow(hwnd)
                import time
                time.sleep(0.1)
            except:
                pass
                
            pyautogui.click(click_x, click_y)
            return {"status": "clicked", "x": click_x, "y": click_y}

        screen_w, screen_h = pyautogui.size()
        click_x = int(screen_w * req.x)
        click_y = int(screen_h * req.y)
        pyautogui.click(click_x, click_y)
        return {"status": "clicked", "x": click_x, "y": click_y}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post('/task')
async def submit_task(request: TaskRequest):
    future = executor.submit(execute_task, request.task)
    try:
        result = future.result(timeout=300)
        logging.info(f"Task completed. Result: {json.dumps(result)}")
        return {"status": "success", "result": result}
    except Exception as exc:
        logging.error(f"Task execution failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

def execute_gemini_cli(task: str) -> dict:
    logging.info(f"Executing Gemini CLI: {task}")
    try:
        result = subprocess.run(["gemini", "-p", task], capture_output=True, text=True, check=True, shell=os.name=='nt')
        res = {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
        logging.info(f"Gemini CLI completed. Result: {json.dumps(res, ensure_ascii=False)}")
        return res
    except Exception as e:
        msg = str(e)
        if isinstance(e, subprocess.CalledProcessError):
            msg += f"\\nStdout: {e.stdout}\\nStderr: {e.stderr}"
        logging.error(f"Gemini CLI failed. Error: {json.dumps({'error': msg}, ensure_ascii=False)}")
        return {"error": msg}

@app.post('/gemini')
async def submit_gemini_task(request: TaskRequest):
    future = executor.submit(execute_gemini_cli, request.task)
    try:
        result = future.result(timeout=300)
        logging.info(f"Gemini Task completed. Result: {json.dumps(result)}")
        return {"status": "success", "result": result}
    except Exception as exc:
        logging.error(f"Gemini Task execution failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

# ─────────────────────────────────────────────────────────
# Task Manager API
# ─────────────────────────────────────────────────────────
TASKS_FILE = Path(r"C:\Users\anton\Sync\Scripts\tasks_agent.json")

def load_tasks_data():
    if not TASKS_FILE.exists():
        return {"tasks": [], "next_id": 1}
    try:
        return json.loads(TASKS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"tasks": [], "next_id": 1}

def save_tasks_data(data):
    TASKS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

class TaskBody(BaseModel):
    text: str

class TaskUpdate(BaseModel):
    text: str | None = None
    done: bool | None = None

class ReorderBody(BaseModel):
    ids: list[int]

@app.get('/tasks')
def get_tasks():
    data = load_tasks_data()
    return {"tasks": data["tasks"]}

@app.post('/tasks')
def add_task(body: TaskBody):
    data = load_tasks_data()
    import datetime
    task = {"id": data["next_id"], "text": body.text, "done": False, "created": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    data["tasks"].insert(0, task)
    data["next_id"] += 1
    save_tasks_data(data)
    return task

@app.put('/tasks/{task_id}')
def update_task(task_id: int, body: TaskUpdate):
    data = load_tasks_data()
    for t in data["tasks"]:
        if t["id"] == task_id:
            if body.text is not None: t["text"] = body.text
            if body.done is not None: t["done"] = body.done
            save_tasks_data(data)
            return t
    raise HTTPException(404, "Task not found")

@app.delete('/tasks/{task_id}')
def delete_task(task_id: int):
    data = load_tasks_data()
    before = len(data["tasks"])
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    if len(data["tasks"]) < before:
        save_tasks_data(data)
        return {"status": "deleted"}
    raise HTTPException(404, "Task not found")

@app.post('/tasks/reorder')
def reorder_tasks(body: ReorderBody):
    data = load_tasks_data()
    tasks_map = {t["id"]: t for t in data["tasks"]}
    new_order = []
    for tid in body.ids:
        if tid in tasks_map:
            new_order.append(tasks_map[tid])
    remaining = [t for t in data["tasks"] if t["id"] not in body.ids]
    data["tasks"] = new_order + remaining
    save_tasks_data(data)
    return {"status": "ok"}

# ─────────────────────────────────────────────────────────
# Agent Dashboard Proxy
# ─────────────────────────────────────────────────────────
AGENT_API_BASE = "http://localhost:8080"

@app.get('/agent', response_class=HTMLResponse)
def get_agent_dashboard():
    return AGENT_DASHBOARD_HTML

@app.get('/api/agent/status')
def proxy_agent_status():
    try:
        r = httpx.get(f"{AGENT_API_BASE}/api/status", timeout=3)
        return Response(content=r.text, media_type="application/json")
    except Exception as e:
        return {"error": str(e), "syncthing": {"status": "offline", "devices": [], "folders": []}, "heartbeat_logs": "Agent dashboard недоступен"}

@app.get('/api/agent/chat')
def proxy_agent_chat():
    try:
        r = httpx.get(f"{AGENT_API_BASE}/api/chat", timeout=3)
        return Response(content=r.text, media_type="application/json")
    except Exception as e:
        return {"chat_room": f"Ошибка подключения к агенту: {e}", "listener_pid": 0, "updated": ""}

@app.post('/api/agent/command')
async def proxy_agent_command(request: Request):
    try:
        body = await request.body()
        r = httpx.post(f"{AGENT_API_BASE}/api/command", content=body, headers={"Content-Type": "application/json"}, timeout=10)
        return Response(content=r.text, media_type="application/json")
    except Exception as e:
        return {"status": "error", "message": f"Ошибка: {e}"}

@app.post('/api/agent/upload')
async def proxy_agent_upload(request: Request):
    try:
        body = await request.body()
        ct = request.headers.get("content-type", "multipart/form-data")
        r = httpx.post(f"{AGENT_API_BASE}/api/upload", content=body, headers={"Content-Type": ct}, timeout=30)
        return Response(content=r.text, media_type="application/json")
    except Exception as e:
        return {"status": "error", "message": f"Ошибка загрузки: {e}"}

@app.post('/api/agent/control')
async def proxy_agent_control(request: Request):
    try:
        body = await request.body()
        r = httpx.post(f"{AGENT_API_BASE}/api/control", content=body, headers={"Content-Type": "application/json"}, timeout=10)
        return Response(content=r.text, media_type="application/json")
    except Exception as e:
        return {"status": "error", "message": f"Ошибка: {e}"}

@app.get('/api/agent/view_file')
def proxy_agent_view_file(path: str = ""):
    try:
        r = httpx.get(f"{AGENT_API_BASE}/api/view_file?path={path}", timeout=5)
        return Response(content=r.content, media_type=r.headers.get("content-type", "application/octet-stream"))
    except Exception as e:
        return Response(content=f"Ошибка: {e}".encode(), status_code=500)

AGENT_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GMC Agent Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #030712;
            --card-bg: rgba(17, 24, 39, 0.7);
            --border-color: rgba(75, 85, 99, 0.2);
            --accent-green: #10b981;
            --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6;
            --accent-red: #ef4444;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg-color);
            background-image: radial-gradient(circle at top right, rgba(59, 130, 246, 0.08), transparent 400px),
                              radial-gradient(circle at bottom left, rgba(139, 92, 246, 0.08), transparent 400px);
            font-family: 'Inter', sans-serif;
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }
        header {
            padding: 24px 40px;
            border-bottom: 1px solid var(--border-color);
            backdrop-filter: blur(12px);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        header h1 {
            font-size: 20px;
            font-weight: 600;
            background: linear-gradient(to right, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .container {
            flex: 1;
            padding: 30px 40px;
            max-width: 1700px;
            margin: 0 auto;
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            backdrop-filter: blur(16px);
            padding: 24px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        .card:hover {
            border-color: rgba(59, 130, 246, 0.3);
            box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.3), 0 0 15px 1px rgba(59, 130, 246, 0.05);
        }
        .status-section { display: flex; flex-direction: column; gap: 20px; }
        .status-item {
            display: flex; align-items: center; justify-content: space-between;
            padding: 12px 16px; background: rgba(31, 41, 55, 0.4);
            border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.03);
        }
        .status-info { display: flex; flex-direction: column; gap: 4px; }
        .status-title { font-size: 13px; color: var(--text-muted); font-weight: 500; }
        .status-val { font-size: 15px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
        .badge {
            display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600;
            padding: 4px 10px; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.05em;
        }
        .badge-online { background: rgba(16, 185, 129, 0.1); color: var(--accent-green); border: 1px solid rgba(16, 185, 129, 0.2); }
        .badge-offline { background: rgba(239, 68, 68, 0.1); color: var(--accent-red); border: 1px solid rgba(239, 68, 68, 0.2); }
        .pulse-dot { width: 8px; height: 8px; border-radius: 50%; background-color: currentColor; animation: pulse 1.5s infinite; }
        @keyframes pulse {
            0% { transform: scale(0.9); opacity: 1; }
            50% { transform: scale(1.2); opacity: 0.5; }
            100% { transform: scale(0.9); opacity: 1; }
        }
        .nav-bar {
            display: flex; gap: 12px; padding: 12px 40px; border-bottom: 1px solid var(--border-color);
            background: rgba(17, 24, 39, 0.5); backdrop-filter: blur(8px);
        }
        .nav-link {
            padding: 8px 16px; border-radius: 8px; font-size: 14px; font-weight: 500;
            color: var(--text-muted); text-decoration: none; transition: all 0.2s;
            border: 1px solid transparent;
        }
        .nav-link:hover { background: rgba(59, 130, 246, 0.1); color: var(--accent-blue); border-color: rgba(59, 130, 246, 0.2); }
        .nav-link.active { background: rgba(59, 130, 246, 0.15); color: var(--accent-blue); border-color: rgba(59, 130, 246, 0.3); }
        .terminal-card { display: flex; flex-direction: column; height: 220px; }
        .terminal-header {
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;
        }
        .terminal-title { font-size: 14px; font-weight: 600; color: var(--text-muted); display: flex; align-items: center; gap: 8px; }
        .terminal-screen {
            flex: 1; background: #030712; border: 1px solid var(--border-color); border-radius: 12px;
            padding: 16px; font-family: 'JetBrains Mono', monospace; font-size: 13.5px;
            line-height: 1.6; overflow-y: auto; color: #e5e7eb; white-space: pre-wrap;
        }
        .chat-room-card { display: flex; flex-direction: column; height: 960px; }
        .chat-room-screen {
            background: rgba(17, 24, 39, 0.4); border: 1px solid var(--border-color); border-radius: 12px;
            padding: 24px; font-size: 16.5px; line-height: 1.65; overflow-y: auto;
            color: #f3f4f6; height: 780px; white-space: pre-wrap;
        }
        .command-box { display: flex; gap: 16px; margin-top: auto; width: 100%; }
        .command-input {
            flex: 1; background: rgba(17, 24, 39, 0.8); border: 1px solid var(--border-color);
            border-radius: 12px; padding: 16px 20px; color: var(--text-main);
            font-family: inherit; font-size: 16.5px; height: 56px; transition: all 0.2s ease;
        }
        .command-input:focus { outline: none; border-color: var(--accent-blue); box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15); }
        .btn {
            background: rgba(59, 130, 246, 0.1); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.2);
            padding: 12px 20px; font-family: inherit; font-size: 14px; font-weight: 500;
            border-radius: 10px; cursor: pointer; transition: all 0.2s ease;
            display: flex; align-items: center; justify-content: center; gap: 8px;
        }
        .btn:hover { background: var(--accent-blue); color: #ffffff; border-color: var(--accent-blue); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2); }
        .btn-secondary {
            background: rgba(156, 163, 175, 0.08); color: #d1d5db; border-color: rgba(156, 163, 175, 0.15);
        }
        .btn-secondary:hover { background: #4b5563; color: #ffffff; border-color: #4b5563; }
        .command-btn { width: auto; white-space: nowrap; }
        .toast {
            position: fixed; bottom: 30px; right: 40px;
            background: rgba(17, 24, 39, 0.95); border: 1px solid var(--accent-blue);
            padding: 16px 24px; border-radius: 12px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            z-index: 1000; display: flex; align-items: center; gap: 12px;
            transform: translateY(100px); opacity: 0; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .toast.show { transform: translateY(0); opacity: 1; }
        .chat-file-link {
            display: inline-flex; align-items: center; gap: 6px;
            background: rgba(139, 92, 246, 0.15); color: #a78bfa !important;
            border: 1px solid rgba(139, 92, 246, 0.3); padding: 4px 12px; border-radius: 8px;
            font-size: 13.5px; font-weight: 600; text-decoration: none !important;
            transition: all 0.2s ease; margin: 2px 0;
        }
        .chat-file-link:hover {
            background: rgba(139, 92, 246, 0.25); border-color: rgba(139, 92, 246, 0.5);
            box-shadow: 0 0 10px rgba(139, 92, 246, 0.2); transform: translateY(-1px);
        }
        @media (max-width: 768px) {
            .container { padding: 16px 12px; gap: 16px; }
            header { padding: 16px 20px; }
            header h1 { font-size: 16px; }
            .card { padding: 16px; border-radius: 12px; }
            .chat-room-card { height: auto; min-height: 600px; }
            .chat-room-screen { padding: 16px; font-size: 14.5px; height: 500px; }
            .command-box { gap: 8px; margin-top: 15px; }
            .command-input { height: 48px; padding: 0 16px; font-size: 14.5px; border-radius: 10px; }
            .command-btn { height: 48px; padding: 0 16px; font-size: 14.5px; border-radius: 10px; }
            .command-btn span { display: none; }
            .nav-bar { padding: 10px 16px; gap: 8px; flex-wrap: wrap; }
            .nav-link { font-size: 13px; padding: 6px 12px; }
        }
    </style>
</head>
<body>
    <header>
        <h1>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M9 1v3"/><path d="M15 1v3"/><path d="M9 20v3"/><path d="M15 20v3"/><path d="M20 9h3"/><path d="M20 15h3"/><path d="M1 9h3"/><path d="M1 15h3"/></svg>
            Global Mission Control Panel
        </h1>
        <div style="font-size: 14px; color: var(--text-muted);" id="local-time">--:--:--</div>
    </header>
    <div class="nav-bar">
        <a href="/" class="nav-link">📋 Control Panel</a>
        <a href="/agent" class="nav-link active">🤖 Agent Chat</a>
        <a href="/view" target="_blank" class="nav-link">📺 Screen</a>
    </div>
    <div class="container">
        <div class="card" style="width: 100%; box-sizing: border-box;">
            <h3 style="font-size: 15px; margin-bottom: 16px; font-weight: 600; color: var(--text-muted); display: flex; align-items: center; gap: 8px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                Статус Syncthing
            </h3>
            <div style="display: flex; flex-direction: column; gap: 12px;" id="syncthing-container">
                <div class="status-item">
                    <div class="status-info">
                        <span class="status-title">Syncthing Service</span>
                        <span class="status-val" id="syncthing-address">-</span>
                    </div>
                    <span class="badge badge-offline" id="syncthing-badge">Offline</span>
                </div>
                <div id="syncthing-devices" style="display: flex; flex-direction: column; gap: 8px; border-top: 1px solid var(--border-color); padding-top: 10px; margin-top: 4px;">
                    <div style="font-size: 11px; color: var(--text-muted);">АКТИВНЫЕ УСТРОЙСТВА:</div>
                    <div style="font-size: 12px; color: var(--text-muted); text-align: center; padding: 5px 0;">Устройства не подключены</div>
                </div>
                <div id="syncthing-folders" style="display: flex; flex-direction: column; gap: 8px; border-top: 1px solid var(--border-color); padding-top: 10px; margin-top: 4px;">
                    <div style="font-size: 11px; color: var(--text-muted);">СИНХРОНИЗАЦИЯ ПАПОК:</div>
                    <div style="font-size: 12px; color: var(--text-muted); text-align: center; padding: 5px 0;">Папки не найдены</div>
                </div>
            </div>
        </div>
        <div class="card terminal-card" style="width: 100%; box-sizing: border-box;">
            <div class="terminal-header">
                <span class="terminal-title">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2H2v10h10V2zM12 12H2v10h10V12zM22 2h-10v10h10V2zM22 12h-10v10h10V12z"/></svg>
                    Консоль Heartbeat (heartbeat.log)
                </span>
                <span style="font-size: 12px; color: var(--text-muted); font-family: monospace;">[Auto-updates every 2s]</span>
            </div>
            <div class="terminal-screen" id="log-screen">Загрузка логов...</div>
        </div>
        <div class="card chat-room-card" style="width: 100%; box-sizing: border-box;">
            <div class="terminal-header">
                <span class="terminal-title" style="color: var(--accent-purple);">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                    Чат GMC (live + syncthing)
                </span>
            </div>
            <div class="chat-room-screen" id="chat-screen">Загрузка...</div>
            <div class="command-box" style="margin-top: 20px; display: flex; gap: 16px; align-items: center; width: 100%;">
                <input type="file" id="file-input" style="display: none;" onchange="uploadFile()">
                <button class="btn btn-secondary" style="width: 56px; height: 56px; padding: 0; display: flex; align-items: center; justify-content: center; border-radius: 12px; flex-shrink: 0;" onclick="document.getElementById('file-input').click()" title="Прикрепить документ">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
                </button>
                <input type="text" class="command-input" id="cmd-input" placeholder="Введите команду или реплику агенту..." onkeydown="if(event.key === 'Enter') sendCommand()" style="flex: 1; height: 56px; font-size: 16.5px; border-radius: 12px; padding: 0 20px; box-sizing: border-box;">
                <button class="btn command-btn" style="height: 56px; padding: 0 28px; font-size: 16.5px; border-radius: 12px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; gap: 8px; width: auto;" onclick="sendCommand()">
                    <span>Отправить</span>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
                </button>
            </div>
        </div>
    </div>
    <div class="toast" id="toast-notify">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>
        <span id="toast-text">-</span>
    </div>
    <script>
        function updateTime() {
            const now = new Date();
            document.getElementById('local-time').innerText = now.toLocaleTimeString('ru-RU');
        }
        setInterval(updateTime, 1000);
        updateTime();

        let autoScrollLogs = true;
        let autoScrollChat = true;

        const logScreen = document.getElementById('log-screen');
        const chatScreen = document.getElementById('chat-screen');

        logScreen.addEventListener('scroll', () => {
            autoScrollLogs = (logScreen.scrollHeight - logScreen.scrollTop - logScreen.clientHeight) < 20;
        });
        chatScreen.addEventListener('scroll', () => {
            autoScrollChat = (chatScreen.scrollHeight - chatScreen.scrollTop - chatScreen.clientHeight) < 20;
        });

        function showToast(text, isError = false) {
            const toast = document.getElementById('toast-notify');
            const toastText = document.getElementById('toast-text');
            toastText.innerText = text;
            toast.style.borderColor = isError ? '#ef4444' : '#3b82f6';
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3000);
        }

        function refreshChat(text, meta) {
            const body = (text && text.trim()) ? text : 'История пуста.';
            chatScreen.textContent = body;
            if (autoScrollChat) chatScreen.scrollTop = chatScreen.scrollHeight;
        }

        async function fetchChat() {
            try {
                const res = await fetch('/api/agent/chat?_=' + Date.now(), { cache: 'no-store' });
                if (!res.ok) throw new Error('HTTP ' + res.status);
                const data = await res.json();
                refreshChat(data.chat_room, data);
                return data;
            } catch (e) {
                console.error('fetchChat failed:', e);
                chatScreen.textContent = 'Ошибка загрузки чата: ' + e.message;
            }
        }

        async function fetchStatus() {
            try {
                const res = await fetch('/api/agent/status?_=' + Date.now(), { cache: 'no-store' });
                if (!res.ok) throw new Error('Network error');
                const data = await res.json();
                try {
                    const syncData = data.syncthing || { status: 'offline', devices: [] };
                    const syncBadge = document.getElementById('syncthing-badge');
                    const syncAddress = document.getElementById('syncthing-address');
                    if (syncData.status === 'online') {
                        syncAddress.innerText = 'PORT 8384';
                        syncBadge.className = 'badge badge-online';
                        syncBadge.innerHTML = '<span class="pulse-dot"></span>Active';
                        const devContainer = document.getElementById('syncthing-devices');
                        devContainer.innerHTML = '<div style="font-size: 11px; color: var(--text-muted); margin-bottom: 4px;">АКТИВНЫЕ УСТРОЙСТВА:</div>';
                        if (syncData.devices && syncData.devices.length > 0) {
                            syncData.devices.forEach(dev => {
                                const devItem = document.createElement('div');
                                devItem.className = 'status-item';
                                devItem.style.fontSize = '12px';
                                devItem.style.padding = '4px 0';
                                const isConn = dev.connected;
                                devItem.innerHTML = '<span style="color: ' + (isConn ? 'var(--text-main)' : 'var(--text-muted)') + '; font-weight: 500;">💻 ' + dev.name + '</span><span class="badge ' + (isConn ? 'badge-online' : 'badge-offline') + '" style="font-size: 10px; padding: 2px 6px;">' + (isConn ? 'Connected' : 'Offline') + '</span>';
                                devContainer.appendChild(devItem);
                            });
                        } else {
                            devContainer.innerHTML += '<div style="font-size: 12px; color: var(--text-muted); text-align: center; padding: 5px 0;">Устройства не подключены</div>';
                        }
                        const foldContainer = document.getElementById('syncthing-folders');
                        foldContainer.innerHTML = '<div style="font-size: 11px; color: var(--text-muted); margin-bottom: 6px;">СИНХРОНИЗАЦИЯ ПАПОК:</div>';
                        if (syncData.folders && syncData.folders.length > 0) {
                            syncData.folders.forEach(fold => {
                                const foldItem = document.createElement('div');
                                foldItem.style.display = 'flex';
                                foldItem.style.flexDirection = 'column';
                                foldItem.style.gap = '6px';
                                foldItem.style.padding = '6px 0';
                                const pctNum = Number(fold.percentage);
                                const pct = Number.isFinite(pctNum) ? pctNum : 0;
                                const barColor = pct === 100 ? 'var(--accent-green)' : 'var(--accent-blue)';
                                foldItem.innerHTML = '<div style="display: flex; justify-content: space-between; font-size: 12px;"><span style="font-weight: 500; color: var(--text-main);">📁 ' + (fold.label || 'folder') + '</span><span style="font-weight: 600; color: ' + barColor + ';">' + pct.toFixed(1) + '%</span></div><div style="width: 100%; height: 6px; background: rgba(255,255,255,0.06); border-radius: 99px; overflow: hidden; border: 1px solid rgba(255,255,255,0.03);"><div style="width: ' + pct + '%; height: 100%; background: ' + barColor + '; border-radius: 99px; transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);"></div></div>';
                                foldContainer.appendChild(foldItem);
                            });
                        } else {
                            foldContainer.innerHTML += '<div style="font-size: 12px; color: var(--text-muted); text-align: center; padding: 5px 0;">Папки не найдены</div>';
                        }
                    } else {
                        syncAddress.innerText = '-';
                        syncBadge.className = 'badge badge-offline';
                        syncBadge.innerHTML = 'Offline';
                        document.getElementById('syncthing-devices').innerHTML = '<div style="font-size: 11px; color: var(--text-muted);">АКТИВНЫЕ УСТРОЙСТВА:</div><div style="font-size: 12px; color: var(--text-muted); text-align: center; padding: 5px 0;">Служба Syncthing не запущена</div>';
                        document.getElementById('syncthing-folders').innerHTML = '<div style="font-size: 11px; color: var(--text-muted);">СИНХРОНИЗАЦИЯ ПАПОК:</div><div style="font-size: 12px; color: var(--text-muted); text-align: center; padding: 5px 0;">Служба Syncthing не запущена</div>';
                    }
                } catch (syncErr) {
                    console.warn('Syncthing UI error:', syncErr);
                }
                logScreen.innerText = data.heartbeat_logs || 'Логи пусты.';
                if (autoScrollLogs) logScreen.scrollTop = logScreen.scrollHeight;
            } catch (e) {
                console.error('Failed to poll status:', e);
            }
        }

        setInterval(fetchStatus, 5000);
        setInterval(fetchChat, 1000);
        fetchChat();
        fetchStatus();

        async function sendCommand() {
            const input = document.getElementById('cmd-input');
            const command = input.value.trim ? input.value.trim() : input.value;
            if (!command) return;
            input.value = '';
            try {
                const res = await fetch('/api/agent/command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command })
                });
                const data = await res.json();
                showToast(data.message, data.status !== 'success');
                if (data.chat_room) {
                    refreshChat(data.chat_room, data);
                } else {
                    await fetchChat();
                }
            } catch (e) {
                showToast('Ошибка отправки команды', true);
            }
        }

        async function uploadFile() {
            const fileInput = document.getElementById('file-input');
            const file = fileInput.files[0];
            if (!file) return;
            showToast('Загрузка файла: ' + file.name + '...');
            const formData = new FormData();
            formData.append('file', file);
            try {
                const res = await fetch('/api/agent/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                showToast(data.message, data.status !== 'success');
                fileInput.value = '';
            } catch (e) {
                showToast('Ошибка загрузки файла', true);
                fileInput.value = '';
            }
        }
    </script>
</body>
</html>"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
