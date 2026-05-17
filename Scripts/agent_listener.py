import os
import time
import subprocess
import socket
import urllib.request
import datetime
import re
import json
import sys
import atexit
import threading

# Global event to trigger instantaneous wakeups on the agent main loop
WAKE_EVENT = threading.Event()

def load_env_vars():
    paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '.hermes', '.env'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),
        os.path.expanduser("~/.hermes/.env"),
        "C:/Users/anton/.hermes/.env"
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, val = line.split('=', 1)
                            os.environ[key.strip()] = val.strip()
            except Exception:
                pass

load_env_vars()

# Устанавливаем принудительный таймаут сокетов для предотвращения зависания при медленных ответах OpenRouter
socket.setdefaulttimeout(35)

# Настройки
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAT_FILE = os.path.join(BASE_DIR, 'ai_chat_room.txt')
LIVE_CHAT_FILE = os.path.join(BASE_DIR, '.gmc_live_chat.txt')
CHAT_IO_LOCK = threading.RLock()
COMMAND_FILE = os.path.join(BASE_DIR, 'agent_commands.txt')
COMMAND_OFFSET_FILE = os.path.join(BASE_DIR, '.agent_commands.offset')
CONTROL_FILE = os.path.join(BASE_DIR, 'agent_control.json')
LOCK_FILE = os.path.join(BASE_DIR, 'agent_listener.lock')
CHAT_HEADER_RE = re.compile(
    r'^\[([^\]]+)\]\s*\[([^\]]+)\]:\s*(.*)$'
)

def normalize_ollama_host(raw_host):
    host = (raw_host or "http://localhost:11434").strip().rstrip("/")
    if host in ("0.0.0.0", "127.0.0.1", "localhost"):
        return "http://localhost:11434"
    if host.startswith("0.0.0.0:"):
        return "http://localhost:" + host.split(":", 1)[1]
    if not host.startswith(("http://", "https://")):
        host = "http://" + host
    return host

def load_ollama_config():
    config_path = os.path.abspath(os.path.join(BASE_DIR, "..", "Configs", "ollama_models.json"))
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

OLLAMA_CONFIG = load_ollama_config()
OLLAMA_HOST = normalize_ollama_host(os.environ.get("OLLAMA_HOST") or OLLAMA_CONFIG.get("host"))
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL") or OLLAMA_CONFIG.get("default_chat_model", "gemma3:latest")
OLLAMA_ROLE_MODELS = OLLAMA_CONFIG.get("role_models", {})
OPENROUTER_ENABLED = os.environ.get("GMC_OPENROUTER_ENABLED", "").lower() in ("1", "true", "yes", "on")
OPENROUTER_HEAVY_ENABLED = os.environ.get("GMC_OPENROUTER_HEAVY", "").lower() in ("1", "true", "yes", "on")
OPENROUTER_TIMEOUT = float(os.environ.get("GMC_OPENROUTER_TIMEOUT", "25"))
OLLAMA_MODEL_PREFERENCES = [
    OLLAMA_MODEL,
    *OLLAMA_CONFIG.get("preferred_chat_models", []),
    "gemma3:latest",
    "gemma2:2b",
    "llama3.2",
    "qwen2.5-coder",
    "llama3",
]
OLLAMA_MODEL_PREFERENCES = list(dict.fromkeys(OLLAMA_MODEL_PREFERENCES))

DEFAULT_CONTROL = {
    "mode": "heavy",
    "forced_model": None,
    "system_instruction": ""
}

def load_agent_control():
    try:
        if os.path.exists(CONTROL_FILE):
            with open(CONTROL_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_CONTROL, **data}
    except Exception:
        pass
    return dict(DEFAULT_CONTROL)

def save_agent_control(control):
    with open(CONTROL_FILE, "w", encoding="utf-8") as f:
        json.dump(control, f, ensure_ascii=False, indent=2)

def apply_agent_control(control=None):
    global OPENROUTER_ENABLED, OPENROUTER_HEAVY_ENABLED
    control = control or load_agent_control()
    mode = control.get("mode", "local")
    OPENROUTER_ENABLED = mode in ("hybrid", "heavy")
    OPENROUTER_HEAVY_ENABLED = mode == "heavy"
    return control

def pid_is_running(pid):
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def acquire_singleton_lock():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r", encoding="utf-8") as f:
                old_pid = (f.read() or "").strip()
            if old_pid.isdigit() and pid_is_running(int(old_pid)):
                print(f"agent_listener.py уже запущен (PID {old_pid}). Команды пишите в {COMMAND_FILE}")
                return False
            print(f"Удаляю устаревший lock (PID {old_pid or '?'} не активен).")
            os.remove(LOCK_FILE)
        except Exception:
            try:
                os.remove(LOCK_FILE)
            except Exception:
                print(f"agent_listener.py уже запущен или lock активен. Команды пишите в {COMMAND_FILE}")
                return False

    fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))

    def cleanup_lock():
        try:
            if os.path.exists(LOCK_FILE):
                with open(LOCK_FILE, "r", encoding="utf-8") as f:
                    if (f.read() or "").strip() == str(os.getpid()):
                        os.remove(LOCK_FILE)
        except Exception:
            pass

    atexit.register(cleanup_lock)
    return True

def read_manual_command():
    """Читает новую команду без сдвига offset — offset фиксируется после успешной обработки."""
    if not os.path.exists(COMMAND_FILE):
        with open(COMMAND_FILE, "w", encoding="utf-8") as f:
            f.write("# Пиши команды ниже. Примеры: /status, /mode local, /model qwen2.5-coder:7b, /system отвечай короче\n")
        return None, None

    offset = 0
    try:
        if os.path.exists(COMMAND_OFFSET_FILE):
            with open(COMMAND_OFFSET_FILE, "r", encoding="utf-8") as f:
                offset = int((f.read() or "0").strip())
    except Exception:
        offset = 0

    size = os.path.getsize(COMMAND_FILE)
    if offset > size:
        offset = 0

    with open(COMMAND_FILE, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(offset)
        new_text = f.read()
        new_offset = f.tell()

    for raw_line in new_text.splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#"):
            return line, new_offset
    return None, None

def commit_manual_command_offset(new_offset):
    if new_offset is None:
        return
    with open(COMMAND_OFFSET_FILE, "w", encoding="utf-8") as f:
        f.write(str(new_offset))

def sender_needs_response(sender):
    if not sender:
        return False
    s = sender.strip().lower()
    if s == DEVICE_NAME.lower():
        return False
    if "gemma" in s or "triage officer" in s or "proactive brain" in s or "gmc proactive" in s:
        return False
    return (
        "denis" in s or "денис" in s or "system" in s
        or "event" in s or "whatsapp" in s or "manual command" in s
    )

def parse_chat_messages(lines):
    """Разбирает чат только по строкам-заголовкам [time] [sender]: text."""
    messages = []
    current = None
    for line in lines:
        m = CHAT_HEADER_RE.match(line.strip())
        if m:
            if current:
                messages.append(current)
            current = {
                "timestamp": m.group(1),
                "sender": m.group(2),
                "body": m.group(3),
            }
        elif current and line.strip():
            current["body"] += "\n" + line.rstrip("\n")
    if current:
        messages.append(current)
    return messages

def find_actionable_chat_line(lines):
    """Последнее сообщение пользователя/System без ответа от этого ПК."""
    messages = parse_chat_messages(lines)
    if not messages:
        return None, None
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if not sender_needs_response(msg["sender"]):
            continue
        answered = any(
            messages[j]["sender"].strip().lower() == DEVICE_NAME.lower()
            for j in range(i + 1, len(messages))
        )
        if answered:
            continue
        full_line = f"[{msg['timestamp']}] [{msg['sender']}]: {msg['body']}"
        return full_line, msg["sender"]
    return None, None

def active_chat_path():
    return LIVE_CHAT_FILE if os.path.exists(LIVE_CHAT_FILE) else CHAT_FILE

def trim_chat_file_if_needed():
    """Архивирует старый чат вместо тихого continue, который блокировал агента."""
    chat_path = active_chat_path()
    if not os.path.exists(chat_path):
        return
    with open(chat_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    if len(lines) <= 200:
        return
    archive = chat_path.replace(".txt", f"_archive_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(archive, "w", encoding="utf-8") as f:
        f.writelines(lines[:-120:])
    with open(chat_path, "w", encoding="utf-8") as f:
        f.writelines(lines[-120:])
    print(f"[Chat] Архив: {archive}, оставлено {min(120, len(lines))} строк.")

def handle_control_command(raw_command):
    command = raw_command.split("]:", 1)[-1].strip() if "]:" in raw_command else raw_command.strip()
    if not command.startswith("/"):
        return None

    control = load_agent_control()
    lower = command.lower()

    if lower == "/status":
        apply_agent_control(control)
        return (
            f"Agent status: mode={control.get('mode')}, "
            f"forced_model={control.get('forced_model') or 'auto'}, "
            f"system_instruction={'set' if control.get('system_instruction') else 'empty'}, "
            f"openrouter={OPENROUTER_ENABLED}, heavy={OPENROUTER_HEAVY_ENABLED}"
        )

    if lower.startswith("/mode "):
        mode = lower.split(maxsplit=1)[1].strip()
        if mode not in ("local", "hybrid", "heavy"):
            return "Режим должен быть: /mode local, /mode hybrid или /mode heavy."
        control["mode"] = mode
        save_agent_control(control)
        apply_agent_control(control)
        return f"Режим агента установлен: {mode}."

    if lower.startswith("/model "):
        model = command.split(maxsplit=1)[1].strip()
        control["forced_model"] = None if model.lower() == "auto" else model
        save_agent_control(control)
        return f"Модель агента: {control['forced_model'] or 'auto'}."

    if lower.startswith("/system "):
        control["system_instruction"] = command.split(maxsplit=1)[1].strip()
        save_agent_control(control)
        return "Пользовательская инструкция сохранена."

    if lower == "/clear-system":
        control["system_instruction"] = ""
        save_agent_control(control)
        return "Пользовательская инструкция очищена."

    return "Команды: /status, /mode local|hybrid|heavy, /model auto|имя, /system текст, /clear-system."

DEVICE_NAME = socket.gethostname()
if 'motorola' in DEVICE_NAME.lower() or 'localhost' in DEVICE_NAME.lower():
    if os.name != 'nt': DEVICE_NAME = 'Termux-Phone'

def get_cli_command():
    if os.name == 'nt':
        npm_path = os.path.join(os.environ.get('APPDATA', ''), 'npm', 'gemini.cmd')
        if os.path.isfile(npm_path): return npm_path
        return "gemini.cmd"
    candidates = [
        os.path.expanduser("/home/denisvalerievichmayorov1/.npm-global/bin/gemini"),
        os.path.expanduser("~/.local/bin/gemini"),
        "/usr/local/bin/gemini",
        "/usr/bin/gemini",
        "gemini"
    ]
    for path in candidates:
        if os.path.isfile(path): return path
    return "gemini"

def register_complaint(action, error_msg):
    """Регистрирует ошибку в централизованном реестре жалоб для Antigravity."""
    complaints_file = os.path.join(BASE_DIR, 'AGENTS_COMPLAINTS.md')
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Создаем файл с заголовком, если его нет
    if not os.path.exists(complaints_file):
        with open(complaints_file, 'w', encoding='utf-8') as f:
            f.write("# 🫵 Реестр жалоб ИИ-Агентов (GMC Complaints Registry)\n\nЭтот файл содержит автоматические жалобы фоновых агентов на ошибки и сбои, требующие оперативного вмешательства и исправления со стороны Antigravity.\n\n")
            
    complaint_entry = f"""
## 🔴 [{DEVICE_NAME}] - {timestamp}
- **Действие:** `{action}`
- **Ошибка:**
  ```text
  {error_msg.strip()}
  ```
- **Статус:** ⏳ Ожидает рассмотрения и исправления от Antigravity.
---
"""
    with open(complaints_file, 'a', encoding='utf-8') as f:
        f.write(complaint_entry)
    print(f"⚠️ Жалоба на '{action}' успешно зарегистрирована in AGENTS_COMPLAINTS.md")

def get_weather():
    try:
        req = urllib.request.Request("https://wttr.in/Antwerp?format=3", headers={'User-Agent': 'curl/7.68.0'})
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8').strip()
    except Exception: return "Нет данных о погоде."

def classify_local_model(prompt, default_role="dispatcher"):
    text = (prompt or "").lower()
    code_markers = [
        "python", "javascript", "node", "powershell", "bash", "script", "скрипт",
        "код", "ошибка", "traceback", "exception", "function", "class", "git",
        "api", "json", "html", "css", "react", "sql", "!run"
    ]
    if any(marker in text for marker in code_markers):
        return OLLAMA_ROLE_MODELS.get("code", "qwen2.5-coder:7b")
    if len(text) > 2500:
        return OLLAMA_ROLE_MODELS.get("general", "llama3.2:latest")
    return OLLAMA_ROLE_MODELS.get(default_role, OLLAMA_MODEL)

def query_local_ollama(prompt, model=None):
    """Локальная Gemma/Ollama через /api/chat (system + user), единый путь с heartbeat."""
    import reasoning_engine
    control = load_agent_control()
    selected = model or control.get("forced_model") or classify_local_model(prompt)
    system_prompt = (
        "Ты — локальный ИИ-помощник Дениса (Gemma/Ollama). Отвечай на русском, кратко и по делу.\n"
        "### Твой процесс:\n"
        "1. Пойми суть запроса (что именно нужно Денису?)\n"
        "2. Если данных не хватает — предложи !google для поика в почте/календаре\n"
        "3. Если есть задача — предложи !run для выполнения или !taskadd для добавления\n"
        "4. Ответь чётко: что сделано / что нужно сделать / какой следующий шаг\n"
        "Избегай воды. Максимум 3-5 предложений."
    )
    return reasoning_engine.query_local_ollama(prompt, system_prompt, model=selected)

def query_openrouter_api(prompt):
    """DeepSeek V4 Flash через OpenRouter, затем openrouter/free."""
    import reasoning_engine
    system_prompt = (
        "Ты — ИИ-советник Дениса с продвинутым reasoning.\n"
        "⚠️ ТЫ РАБОТАЕШЬ ТОЛЬКО ПО ЗАДАЧАМ ИЗ ФАЙЛА tasks_agent.json.\n"
        "Если в списке есть задача — выполни её через !run или !google. Если задачи нет — не предпринимай действий и напиши «Нет задачи в списке.»\n"
        "Если хочешь предложить новую задачу — напиши '!taskadd: <текст>' чтобы Денис сам решил.\n\n"
        "### Твой процесс рассуждения (System 2):\n"
        "1. **Анализ**: Какая задача активна? Какой контекст (WhatsApp, почта, чат)?\n"
        "2. **Планирование**: Разбей задачу на шаги. Какой инструмент нужен (!run, !google)?\n"
        "3. **Самопроверка**: Не повторяешь ли прошлый ответ? Учтены ли все детали?\n"
        "4. **Исполнение**: Конкретное действие или рекомендация.\n\n"
        "Формат ответа:\n"
        "1. 💭 **Анализ:** (шаги 1-3, 2-3 предложения)\n"
        "2. 👉 **Действие:** (шаг 4, что делать прямо сейчас)\n"
        "Отвечай на русском. Максимум 5-7 строк. Без вопросов Денису."
    )
    return reasoning_engine.query_openrouter(
        prompt,
        system_prompt,
        model=reasoning_engine.DEFAULT_MODEL,
    )

def check_and_start_ollama():
    """Проверяет доступность Ollama и запускает сервис, если он недоступен."""
    import requests
    try:
        requests.get("http://localhost:11434/api/tags", timeout=3)
        print("✅ Ollama уже запущена.")
    except:
        print("⚠️ Ollama не отвечает. Попытка запуска...")
        subprocess.Popen([r"C:\Users\anton\AppData\Local\Programs\Ollama\ollama app.exe"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        time.sleep(10) # Ждем загрузки

# =====================================================================
# INTERACTIVE WEB DASHBOARD SERVER (http://localhost:8080)
# =====================================================================

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global Mission Control Dashboard</title>
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
        .status-section {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .status-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            background: rgba(31, 41, 55, 0.4);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.03);
        }
        .status-info { display: flex; flex-direction: column; gap: 4px; }
        .status-title { font-size: 13px; color: var(--text-muted); font-weight: 500; }
        .status-val { font-size: 15px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 9999px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .badge-online { background: rgba(16, 185, 129, 0.1); color: var(--accent-green); border: 1px solid rgba(16, 185, 129, 0.2); }
        .badge-offline { background: rgba(239, 68, 68, 0.1); color: var(--accent-red); border: 1px solid rgba(239, 68, 68, 0.2); }
        .pulse-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: currentColor;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.9); opacity: 1; }
            50% { transform: scale(1.2); opacity: 0.5; }
            100% { transform: scale(0.9); opacity: 1; }
        }
        .btn {
            background: rgba(59, 130, 246, 0.1);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.2);
            padding: 12px 20px;
            font-family: inherit;
            font-size: 14px;
            font-weight: 500;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            width: 100%;
        }
        .btn:hover {
            background: var(--accent-blue);
            color: #ffffff;
            border-color: var(--accent-blue);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
        }
        .btn-danger {
            background: rgba(239, 68, 68, 0.08);
            color: #f87171;
            border-color: rgba(239, 68, 68, 0.15);
        }
        .btn-danger:hover {
            background: var(--accent-red);
            color: #ffffff;
            border-color: var(--accent-red);
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
        }
        .btn-secondary {
            background: rgba(156, 163, 175, 0.08);
            color: #d1d5db;
            border-color: rgba(156, 163, 175, 0.15);
        }
        .btn-secondary:hover {
            background: #4b5563;
            color: #ffffff;
            border-color: #4b5563;
        }
        .action-grid { display: flex; flex-direction: column; gap: 12px; margin-top: 10px; }
        .main-content {
            display: flex;
            flex-direction: column;
            gap: 30px;
        }
        .terminal-card {
            display: flex;
            flex-direction: column;
            height: 220px;
        }
        .terminal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .terminal-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .terminal-screen {
            flex: 1;
            background: #030712;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13.5px;
            line-height: 1.6;
            overflow-y: auto;
            color: #e5e7eb;
            white-space: pre-wrap;
        }
        .chat-room-card {
            display: flex;
            flex-direction: column;
            height: 960px;
        }
        .chat-room-screen {
            background: rgba(17, 24, 39, 0.4);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            font-size: 16.5px;
            line-height: 1.65;
            overflow-y: auto;
            color: #f3f4f6;
            height: 780px;
            white-space: pre-wrap;
        }
        .command-box {
            display: flex;
            gap: 16px;
            margin-top: auto;
            width: 100%;
        }
        .command-input {
            flex: 1;
            background: rgba(17, 24, 39, 0.8);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px 20px;
            color: var(--text-main);
            font-family: inherit;
            font-size: 16.5px;
            height: 56px;
            transition: all 0.2s ease;
        }
        .command-input:focus {
            outline: none;
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
        }
        .command-btn {
            width: auto;
            white-space: nowrap;
        }
        .toast {
            position: fixed;
            bottom: 30px;
            right: 40px;
            background: rgba(17, 24, 39, 0.95);
            border: 1px solid var(--accent-blue);
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 12px;
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .toast.show { transform: translateY(0); opacity: 1; }
        
        @media (max-width: 768px) {
            .container {
                padding: 16px 12px;
                gap: 16px;
            }
            header {
                padding: 16px 20px;
            }
            header h1 {
                font-size: 16px;
            }
            .card {
                padding: 16px;
                border-radius: 12px;
            }
            .chat-room-card {
                height: auto;
                min-height: 600px;
            }
            .chat-room-screen {
                padding: 16px;
                font-size: 14.5px;
                height: 500px;
            }
            .command-box {
                gap: 8px;
                margin-top: 15px;
            }
            .command-input {
                height: 48px;
                padding: 0 16px;
                font-size: 14.5px;
                border-radius: 10px;
            }
            .command-btn {
                height: 48px;
                padding: 0 16px;
                font-size: 14.5px;
                border-radius: 10px;
                width: auto;
            }
            .command-btn span {
                display: none; /* Hide the 'Отправить' text on mobile */
            }
            .command-btn svg {
                margin-left: 0 !important;
            }
            .btn-secondary {
                height: 48px !important;
                width: 48px !important;
                border-radius: 10px !important;
            }
            .status-item {
                padding: 10px 12px;
            }
            .status-title {
                font-size: 12px;
            }
            .status-val {
                font-size: 13.5px;
            }
            .badge {
                font-size: 10px;
                padding: 3px 8px;
            }
        }
        .chat-file-link {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(139, 92, 246, 0.15);
            color: #a78bfa !important;
            border: 1px solid rgba(139, 92, 246, 0.3);
            padding: 4px 12px;
            border-radius: 8px;
            font-size: 13.5px;
            font-weight: 600;
            text-decoration: none !important;
            transition: all 0.2s ease;
            margin: 2px 0;
        }
        .chat-file-link:hover {
            background: rgba(139, 92, 246, 0.25);
            border-color: rgba(139, 92, 246, 0.5);
            box-shadow: 0 0 10px rgba(139, 92, 246, 0.2);
            transform: translateY(-1px);
        }
        .chat-web-link {
            color: #60a5fa !important;
            font-weight: 500;
            text-decoration: underline !important;
            transition: color 0.2s ease;
        }
        .chat-web-link:hover {
            color: #93c5fd !important;
        }
    </style>
</head>
<body>
    <header>
        <h1>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-cpu"><rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M9 1v3"/><path d="M15 1v3"/><path d="M9 20v3"/><path d="M15 20v3"/><path d="M20 9h3"/><path d="M20 15h3"/><path d="M1 9h3"/><path d="M1 15h3"/></svg>
            Global Mission Control Panel
        </h1>
        <div style="font-size: 14px; color: var(--text-muted);" id="local-time">--:--:--</div>
    </header>
    
    <div class="container">
        <!-- Статус Syncthing (100% ширина, в одну колонку) -->
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
        
        <!-- Информационный чат-рум (100% ширина, увеличенные шрифты и ввод) -->
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

        let autoScrollChat = true;

        const chatScreen = document.getElementById('chat-screen');

        chatScreen.addEventListener('scroll', () => {
            autoScrollChat = (chatScreen.scrollHeight - chatScreen.scrollTop - chatScreen.clientHeight) < 20;
        });

        function showToast(text, isError = false) {
            const toast = document.getElementById('toast-notify');
            const toastText = document.getElementById('toast-text');
            toastText.innerText = text;
            if (isError) {
                toast.style.borderColor = '#ef4444';
            } else {
                toast.style.borderColor = '#3b82f6';
            }
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }

        function refreshChat(text, meta) {
            const body = (text && text.trim()) ? text : 'История пуста.';
            chatScreen.textContent = body;
            if (autoScrollChat) {
                chatScreen.scrollTop = chatScreen.scrollHeight;
            }
        }

        async function fetchChat() {
            try {
                const res = await fetch('/api/chat?_=' + Date.now(), { cache: 'no-store' });
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
                const res = await fetch('/api/status?_=' + Date.now(), { cache: 'no-store' });
                if (!res.ok) throw new Error('Network error');
                const data = await res.json();
                
                // (Служебная телеметрия удалена по запросу)

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
                            devItem.innerHTML = `
                                <span style="color: ${isConn ? 'var(--text-main)' : 'var(--text-muted)'}; font-weight: 500;">💻 ${dev.name}</span>
                                <span class="badge ${isConn ? 'badge-online' : 'badge-offline'}" style="font-size: 10px; padding: 2px 6px;">
                                    ${isConn ? 'Connected' : 'Offline'}
                                </span>
                            `;
                            devContainer.appendChild(devItem);
                        });
                    } else {
                        devContainer.innerHTML += '<div style="font-size: 12px; color: var(--text-muted); text-align: center; padding: 5px 0;">Устройства не подключены</div>';
                    }

                    // Render folders completion stats with progress bars
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
                            
                            foldItem.innerHTML = `
                                <div style="display: flex; justify-content: space-between; font-size: 12px;">
                                    <span style="font-weight: 500; color: var(--text-main);">📁 ${fold.label || 'folder'}</span>
                                    <span style="font-weight: 600; color: ${barColor};">${pct.toFixed(1)}%</span>
                                </div>
                                <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.06); border-radius: 99px; overflow: hidden; border: 1px solid rgba(255,255,255,0.03);">
                                    <div style="width: ${pct}%; height: 100%; background: ${barColor}; border-radius: 99px; transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);"></div>
                                </div>
                            `;
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

            } catch (e) {
                console.error('Failed to poll status:', e);
            }
        }

        setInterval(fetchStatus, 5000);
        setInterval(fetchChat, 1000);
        fetchChat();
        fetchStatus();

        async function triggerAction(action) {
            if (action === 'restart') {
                document.getElementById('btn-restart').innerText = 'Перезапуск...';
            }
            try {
                const res = await fetch('/api/control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action })
                });
                const data = await res.json();
                showToast(data.message);
                if (action === 'restart') {
                    setTimeout(() => {
                        window.location.reload();
                    }, 4000);
                }
            } catch (e) {
                showToast('Ошибка при отправке запроса', true);
            }
        }

        async function sendCommand() {
            const input = document.getElementById('cmd-input');
            const command = input.value.trim ? input.value.trim() : input.value;
            if (!command) return;
            
            input.value = '';
            try {
                const res = await fetch('/api/command', {
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
                const res = await fetch('/api/upload', {
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

COMBINED_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GMC Combined Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #030712; --card-bg: rgba(17,24,39,0.7);
            --border-color: rgba(75,85,99,0.2); --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6; --text-main: #f3f4f6; --text-muted: #9ca3af;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background: var(--bg-color); color: var(--text-main);
            font-family: 'Inter', sans-serif; min-height: 100vh;
            display: flex; flex-direction: column;
        }
        header {
            padding: 20px 32px; border-bottom: 1px solid var(--border-color);
            backdrop-filter: blur(12px);
        }
        header h1 { font-size: 18px; font-weight: 600; background: linear-gradient(to right, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .nav-bar {
            display: flex; gap: 8px; padding: 10px 32px;
            border-bottom: 1px solid var(--border-color); background: rgba(17,24,39,0.5);
        }
        .nav-link {
            padding: 8px 16px; border-radius: 8px; font-size: 14px; font-weight: 500;
            color: var(--text-muted); text-decoration: none; cursor: pointer;
            border: 1px solid transparent; transition: all 0.2s;
        }
        .nav-link:hover { background: rgba(59,130,246,0.1); color: var(--accent-blue); border-color: rgba(59,130,246,0.2); }
        .nav-link.active { background: rgba(59,130,246,0.15); color: var(--accent-blue); border-color: rgba(59,130,246,0.3); }
        .container { flex: 1; padding: 20px 32px; display: flex; flex-direction: column; gap: 16px; }
        .tabs { display: flex; gap: 4px; }
        .tab-btn { padding: 10px 20px; border: none; background: #1e293b; color: #94a3b8; border-radius: 8px 8px 0 0; cursor: pointer; font-weight: 600; font-size: 14px; }
        .tab-btn.active { background: var(--card-bg); color: var(--text-main); }
        .tab-content { display: none; flex: 1; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 0 12px 12px 12px; padding: 20px; }
        .tab-content.active { display: flex; flex-direction: column; gap: 16px; }
        iframe { width: 100%; flex: 1; border: none; border-radius: 8px; background: #000; min-height: 600px; }
        .log-view { background: #030712; border: 1px solid var(--border-color); border-radius: 8px; padding: 12px; font-family: monospace; font-size: 13px; overflow-y: auto; max-height: 400px; white-space: pre-wrap; color: #e5e7eb; }
    </style>
</head>
<body>
    <header><h1>Global Mission Control — Combined Panel</h1></header>
    <div class="nav-bar">
        <a href="/" class="nav-link">🤖 Agent Dashboard</a>
        <a href="/panel" class="nav-link active">📊 Combined Panel</a>
        <a href="http://localhost:8000/view" target="_blank" class="nav-link">📺 Screen</a>
    </div>
    <div class="container">
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('agent')">🤖 Agent Chat</button>
            <button class="tab-btn" onclick="switchTab('control')">🎛 Control Panel</button>
        </div>
        <div class="tab-content active" id="tab-agent">
            <div style="display:flex;flex-direction:column;gap:16px;flex:1;">
                <div style="display:flex;gap:12px;">
                    <input type="text" id="cmd-input" placeholder="Введите команду агенту..." style="flex:1;padding:12px;border-radius:8px;border:1px solid var(--border-color);background:rgba(17,24,39,0.8);color:var(--text-main);font-size:15px;" onkeydown="if(event.key==='Enter') sendCommand()">
                    <input type="file" id="file-input" style="display:none" onchange="uploadFile()">
                    <button onclick="document.getElementById('file-input').click()" style="padding:12px;border-radius:8px;border:1px solid var(--border-color);background:rgba(156,163,175,0.08);color:#d1d5db;cursor:pointer;">📎</button>
                    <button onclick="sendCommand()" style="padding:12px 24px;border-radius:8px;border:none;background:var(--accent-blue);color:white;font-weight:600;cursor:pointer;">Отправить</button>
                </div>
                <div class="log-view" id="chat-screen" style="max-height:none;flex:1;min-height:500px;">Загрузка...</div>
            </div>
        </div>
        <div class="tab-content" id="tab-control">
            <div style="display:flex;flex-direction:column;gap:12px;flex:1;">
                <div style="display:flex;gap:8px;">
                    <input type="text" id="task-input" placeholder="New task..." style="flex:1;padding:10px;border-radius:6px;border:1px solid var(--border-color);background:#0f172a;color:white;font-size:14px;">
                    <button onclick="addTask()" style="padding:10px 16px;border-radius:6px;border:none;background:#10b981;color:white;font-weight:600;cursor:pointer;">+ Add</button>
                </div>
                <div id="task-list" style="display:flex;flex-direction:column;gap:6px;"></div>
                <div style="display:flex;gap:8px;justify-content:space-between;align-items:center;">
                    <span id="task-counter" style="font-size:13px;color:var(--text-muted);">0 active</span>
                    <button onclick="fetchLogs()" style="padding:6px 12px;border-radius:6px;border:1px solid var(--border-color);background:transparent;color:var(--text-muted);cursor:pointer;font-size:13px;">🔄 Refresh Logs</button>
                </div>
                <div class="log-view" id="logs-view" style="flex:1;min-height:300px;">Загрузка логов...</div>
            </div>
        </div>
    </div>
    <script>
        let showDone = false;

        function switchTab(tab) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.textContent.includes(tab==='agent'?'Agent':'Control')));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.toggle('active', c.id==='tab-'+tab));
            if (tab==='control') { loadTasks(); fetchLogs(); }
            if (tab==='agent') fetchChat();
        }

        // Agent chat via local endpoints
        async function fetchChat() {
            try {
                const r = await fetch('/api/chat?_='+Date.now(), {cache:'no-store'});
                const d = await r.json();
                document.getElementById('chat-screen').textContent = d.chat_room || 'Пусто.';
            } catch(e) { document.getElementById('chat-screen').textContent = 'Ошибка: '+e.message; }
        }
        setInterval(fetchChat, 2000);
        fetchChat();

        async function sendCommand() {
            const input = document.getElementById('cmd-input');
            const cmd = input.value.trim();
            if (!cmd) return;
            input.value = '';
            try {
                const r = await fetch('/api/command', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({command:cmd})});
                const d = await r.json();
                await fetchChat();
            } catch(e) { console.error(e); }
        }

        async function uploadFile() {
            const fileInput = document.getElementById('file-input');
            const file = fileInput.files[0];
            if (!file) return;
            const fd = new FormData();
            fd.append('file', file);
            try {
                await fetch('/api/upload', {method:'POST', body:fd});
                fileInput.value = '';
                await fetchChat();
            } catch(e) { console.error(e); }
        }

        // Tasks via proxy to 8000
        async function loadTasks() {
            try {
                const r = await fetch('/api/panel/tasks?_='+Date.now(), {cache:'no-store'});
                const d = await r.json();
                const list = document.getElementById('task-list');
                const counter = document.getElementById('task-counter');
                const active = (d.tasks||[]).filter(t=>!t.done).length;
                counter.textContent = active + ' active / ' + (d.tasks||[]).length + ' total';
                const tasks = showDone ? d.tasks : (d.tasks||[]).filter(t=>!t.done);
                list.innerHTML = tasks.map(t => '<div style="display:flex;align-items:center;gap:8px;padding:8px 10px;background:#0f172a;border-radius:6px;border:1px solid #334155;opacity:'+(t.done?'0.5':'1')+'"><input type="checkbox" '+(t.done?'checked':'')+' onchange="toggleTask('+t.id+',this.checked)"><span style="flex:1;'+(t.done?'text-decoration:line-through':'')+'">'+t.text+'</span><button onclick="deleteTask('+t.id+')" style="padding:2px 8px;border-radius:4px;border:none;background:#ef4444;color:white;cursor:pointer;font-size:12px;">✕</button></div>').join('');
            } catch(e) { document.getElementById('task-list').innerHTML = 'Ошибка: '+e.message; }
        }

        async function addTask() {
            const input = document.getElementById('task-input');
            const text = input.value.trim();
            if (!text) return;
            input.value = '';
            await fetch('/api/panel/tasks', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text})});
            loadTasks();
        }

        async function deleteTask(id) {
            await fetch('/api/panel/tasks/'+id, {method:'DELETE'});
            loadTasks();
        }

        async function toggleTask(id, done) {
            await fetch('/api/panel/tasks/'+id, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({done})});
            loadTasks();
        }

        async function fetchLogs() {
            try {
                const r = await fetch('/api/panel/logs?_='+Date.now(), {cache:'no-store'});
                const d = await r.json();
                document.getElementById('logs-view').innerHTML = d.logs || 'Нет логов.';
            } catch(e) { document.getElementById('logs-view').innerHTML = 'Ошибка: '+e.message; }
        }
        setInterval(fetchLogs, 3000);
        fetchLogs();
    </script>
</body>
</html>"""

SYNCTHING_CACHE = {
    "status": "offline",
    "devices": [],
    "folders": []
}
SYNCTHING_LOCK = threading.Lock()

def get_syncthing_status_raw():
    import xml.etree.ElementTree as ET
    import urllib.request
    import json
    
    result = {
        "status": "offline",
        "devices": [],
        "folders": []
    }
    
    local_app_data = os.environ.get("LOCALAPPDATA", r"C:\Users\anton\AppData\Local")
    config_path = os.path.join(local_app_data, "Syncthing", "config.xml")
    if not os.path.exists(config_path):
        return result
        
    try:
        tree = ET.parse(config_path)
        root = tree.getroot()
        gui = root.find('gui')
        apikey = gui.find('apikey').text
        address = gui.find('address').text
        
        if ":" in address:
            port = address.split(":")[-1]
        else:
            port = "8384"
            
        url_base = f"http://127.0.0.1:{port}"
        
        req_sys = urllib.request.Request(f"{url_base}/rest/system/status")
        req_sys.add_header('X-API-Key', apikey)
        with urllib.request.urlopen(req_sys, timeout=0.2) as response:
            sys_data = json.loads(response.read().decode('utf-8'))
            result["status"] = "online"
            
        req_conn = urllib.request.Request(f"{url_base}/rest/system/connections")
        req_conn.add_header('X-API-Key', apikey)
        with urllib.request.urlopen(req_conn, timeout=0.2) as response:
            conn_data = json.loads(response.read().decode('utf-8'))
            
        req_dev = urllib.request.Request(f"{url_base}/rest/config/devices")
        req_dev.add_header('X-API-Key', apikey)
        with urllib.request.urlopen(req_dev, timeout=0.2) as response:
            dev_data = json.loads(response.read().decode('utf-8'))
            
        dev_map = {d["deviceID"]: d.get("name", "Unknown") for d in dev_data}
        
        connections = conn_data.get("connections", {})
        for dev_id, conn in connections.items():
            if dev_id in dev_map and dev_map[dev_id].lower() != "desktop-85d3nji":
                name = dev_map[dev_id]
                connected = conn.get("connected", False)
                result["devices"].append({
                    "name": name,
                    "connected": connected,
                    "address": conn.get("address", "")
                })
                
        # Получаем данные о синхронизации по каждой папке
        result["folders"] = []
        try:
            req_fold = urllib.request.Request(f"{url_base}/rest/config/folders")
            req_fold.add_header('X-API-Key', apikey)
            with urllib.request.urlopen(req_fold, timeout=0.2) as response:
                fold_data = json.loads(response.read().decode('utf-8'))
                
            for fold in fold_data:
                fold_id = fold["id"]
                fold_label = fold.get("label") or fold_id
                
                percent = 100.0
                try:
                    req_comp = urllib.request.Request(f"{url_base}/rest/db/completion?folder={fold_id}")
                    req_comp.add_header('X-API-Key', apikey)
                    with urllib.request.urlopen(req_comp, timeout=0.2) as response:
                        comp_data = json.loads(response.read().decode('utf-8'))
                        percent = float(comp_data.get("completion", 100.0))
                except Exception:
                    pass
                    
                result["folders"].append({
                    "id": fold_id,
                    "label": fold_label,
                    "percentage": percent
                })
        except Exception:
            pass
    except Exception:
        pass
        
    return result

def start_syncthing_poller():
    def poll_loop():
        global SYNCTHING_CACHE
        try:
            res = get_syncthing_status_raw()
            with SYNCTHING_LOCK:
                SYNCTHING_CACHE = res
        except Exception:
            pass
        while True:
            try:
                latest = get_syncthing_status_raw()
                with SYNCTHING_LOCK:
                    SYNCTHING_CACHE = latest
            except Exception:
                pass
            time.sleep(10)
            
    t = threading.Thread(target=poll_loop, daemon=True)
    t.start()

def get_syncthing_status():
    with SYNCTHING_LOCK:
        return SYNCTHING_CACHE

def read_dashboard_chat(max_lines=120):
    """Текст чата для веб-панели: live-файл + резерв syncthing."""
    chunks = []
    for path in (LIVE_CHAT_FILE, CHAT_FILE):
        if not os.path.exists(path):
            continue
        try:
            acquired = CHAT_IO_LOCK.acquire(timeout=2.0)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                chunks.append("".join(lines[-max_lines:]))
            finally:
                if acquired:
                    CHAT_IO_LOCK.release()
        except Exception as e:
            chunks.append(f"[Ошибка чтения {os.path.basename(path)}: {e}]\n")
    if not chunks:
        return ""
    if len(chunks) == 1:
        return chunks[0]
    return chunks[0] + "\n--- sync ---\n" + chunks[1][-8000:]

def get_system_status():
    import psutil
    status = {
        "listener_pid": os.getpid(),
        "listener_status": "online",
        "heartbeat_pid": None,
        "heartbeat_status": "offline",
        "proactive_brain": os.environ.get("GMC_PROACTIVE_BRAIN", "0") in ("1", "true", "yes", "on"),
        "heartbeat_logs": "",
        "chat_room": read_dashboard_chat(),
        "syncthing": get_syncthing_status()
    }
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if p.info['name'] and p.info['name'].lower() == 'python.exe':
                cmdline = p.info['cmdline'] or []
                if any('heartbeat.py' in x.lower() for x in cmdline):
                    status["heartbeat_pid"] = p.info['pid']
                    status["heartbeat_status"] = "online"
                    break
        except Exception:
            pass
            
    log_path = os.path.join(BASE_DIR, 'heartbeat.log')
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                status["heartbeat_logs"] = "".join(lines[-200:])
        except Exception as e:
            status["heartbeat_logs"] = f"Ошибка чтения лога: {e}"
    else:
        status["heartbeat_logs"] = "Лог-файл еще не создан."
        
    return status

def json_response(handler, payload, status_code=200):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
    handler.end_headers()
    handler.wfile.write(body)

def handle_system_action(action):
    import threading
    if action == 'restart':
        def reboot_thread():
            import time
            time.sleep(1)
            import psutil
            for p in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if p.info['name'] and p.info['name'].lower() == 'python.exe':
                        cmdline = p.info['cmdline'] or []
                        if any('heartbeat.py' in x.lower() for x in cmdline):
                            p.kill()
                except Exception:
                    pass
            lock_path = os.path.join(BASE_DIR, 'agent_listener.lock')
            if os.path.exists(lock_path):
                try:
                    os.remove(lock_path)
                except Exception:
                    pass
            subprocess.Popen(['python', os.path.join(BASE_DIR, 'agent_listener.py')], creationflags=0x08000000)
            os.kill(os.getpid(), 9)
            
        threading.Thread(target=reboot_thread, daemon=True).start()
        return {"status": "success", "message": "Службы перезапускаются..."}
        
    elif action == 'stop':
        def stop_thread():
            import time
            time.sleep(1)
            import psutil
            for p in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if p.info['name'] and p.info['name'].lower() == 'python.exe':
                        cmdline = p.info['cmdline'] or []
                        if any('heartbeat.py' in x.lower() for x in cmdline):
                            p.kill()
                except Exception:
                    pass
            lock_path = os.path.join(BASE_DIR, 'agent_listener.lock')
            if os.path.exists(lock_path):
                try:
                    os.remove(lock_path)
                except Exception:
                    pass
            os.kill(os.getpid(), 9)
            
        threading.Thread(target=stop_thread, daemon=True).start()
        return {"status": "success", "message": "Службы останавливаются..."}
        
    elif action == 'clear_logs':
        log_path = os.path.join(BASE_DIR, 'heartbeat.log')
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [System]: Logs cleared via Dashboard.\\n")
            return {"status": "success", "message": "Логи успешно очищены!"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    return {"status": "error", "message": "Неизвестное действие."}

def append_chat_line(sender, text, mirror_sync=True):
    """Пишет в локальный live-чат (для панели) и опционально в syncthing-файл."""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] [{sender}]: {text}\n"
    with CHAT_IO_LOCK:
        for path in (LIVE_CHAT_FILE, CHAT_FILE if mirror_sync else None):
            if not path:
                continue
            try:
                with open(path, 'a', encoding='utf-8') as f:
                    f.write(f"\n{line}" if not line.startswith('\n') else line)
            except Exception as e:
                print(f"[Chat] Ошибка записи {path}: {e}")
    return line

def process_command_immediate(cmd):
    """Синхронный быстрый ответ для панели — не ждём фоновый цикл."""
    cmd = (cmd or "").strip()
    if not cmd:
        return "Пустая команда."
    if cmd.startswith("/"):
        return handle_control_command(f"[Manual Command]: {cmd}") or "Неизвестная команда."
    if cmd.lower().startswith("!google"):
        return "Принял. Выполняю запрос к Google (см. ответ в чате через несколько секунд)..."
    if cmd.lower().startswith("!run"):
        return "Принял. Запуск скрипта обрабатывается фоновым агентом..."
    reply = query_local_ollama(
        f"Денис написал: «{cmd}»\nОтветь по-русски, 1–3 предложения, конкретно."
    )
    return reply or f"Принял: «{cmd}». Локальная Gemma отвечает, подождите пару секунд."

def handle_send_command(cmd):
    try:
        cmd = (cmd or "").strip()
        with open(COMMAND_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{cmd}\n")
        new_offset = os.path.getsize(COMMAND_FILE)
        commit_manual_command_offset(new_offset)

        append_chat_line("Денис", cmd)

        reply = process_command_immediate(cmd)
        append_chat_line(DEVICE_NAME, reply)

        WAKE_EVENT.set()
        return {
            "status": "success",
            "message": "Ответ в чате.",
            "chat_room": read_dashboard_chat(max_lines=120),
            "listener_pid": os.getpid(),
            "updated": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = False
class DashboardHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    def do_GET(self):
        if self.path == '/' or self.path.startswith('/?'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode('utf-8'))
        elif self.path == '/api/status' or self.path.startswith('/api/status?'):
            json_response(self, get_system_status())
        elif self.path == '/api/chat' or self.path.startswith('/api/chat?'):
            json_response(self, {
                "chat_room": read_dashboard_chat(),
                "listener_pid": os.getpid(),
                "updated": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            })
        elif self.path.startswith('/api/view_file'):
            import urllib.parse
            query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            file_path = query_components.get('path', [''])[0]
            if file_path and os.path.exists(file_path):
                normalized_path = os.path.normpath(file_path)
                # Разрешаем просмотр файлов в домашнем каталоге пользователя
                if normalized_path.lower().startswith("c:\\users\\anton"):
                    self.send_response(200)
                    ext = os.path.splitext(normalized_path)[1].lower()
                    if ext == '.pdf':
                        self.send_header('Content-Type', 'application/pdf')
                    elif ext in ('.png', '.jpg', '.jpeg', '.webp'):
                        self.send_header('Content-Type', f'image/{ext[1:]}')
                    elif ext in ('.txt', '.log', '.py', '.sh', '.bat', '.json', '.xml', '.html', '.md'):
                        self.send_header('Content-Type', 'text/plain; charset=utf-8')
                    else:
                        self.send_header('Content-Type', 'application/octet-stream')
                    
                    file_size = os.path.getsize(normalized_path)
                    self.send_header('Content-Length', str(file_size))
                    self.end_headers()
                    
                    with open(normalized_path, 'rb') as f:
                        self.wfile.write(f.read())
                    return
            self.send_response(404)
            self.end_headers()
        elif self.path == '/panel' or self.path.startswith('/panel?'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(COMBINED_HTML.encode('utf-8'))
        elif self.path.startswith('/api/panel/'):
            # Proxy to antigravity server on 8000
            import urllib.request
            target_path = self.path.replace('/api/panel/', '/', 1)
            if self.path.startswith('/api/panel/tasks/') or self.path.startswith('/api/panel/logs') or self.path.startswith('/api/panel/screen') or self.path.startswith('/api/panel/click') or self.path.startswith('/api/panel/task') or self.path.startswith('/api/panel/gemini') or self.path.startswith('/api/panel/view'):
                target_url = f"http://localhost:8000{target_path}"
                try:
                    proxy_resp = urllib.request.urlopen(target_url, timeout=5)
                    content = proxy_resp.read()
                    self.send_response(proxy_resp.status)
                    resp_content_type = proxy_resp.headers.get('Content-Type', 'application/octet-stream')
                    self.send_header('Content-Type', resp_content_type)
                    if resp_content_type == 'application/json':
                        self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(content)
                except Exception as e:
                    self.send_response(502)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Proxy error: {e}"}).encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
            
    def do_POST(self):
        content_type = self.headers.get('Content-Type', '')
        content_length = int(self.headers.get('Content-Length', 0))
        
        if self.path == '/api/upload' and 'multipart/form-data' in content_type:
            try:
                body = self.rfile.read(content_length)
                from email.parser import BytesParser
                from email.policy import default
                raw_msg = b"Content-Type: " + content_type.encode('utf-8') + b"\r\n\r\n" + body
                msg = BytesParser(policy=default).parsebytes(raw_msg)
                
                uploaded_file = None
                filename = None
                for part in msg.iter_parts():
                    fn = part.get_filename()
                    if fn:
                        filename = fn
                        uploaded_file = part.get_payload(decode=True)
                        break
                
                if filename and uploaded_file is not None:
                    import urllib.parse
                    filename = urllib.parse.unquote(filename)
                    upload_dir = os.path.join(os.path.dirname(BASE_DIR), 'downloads')
                    os.makedirs(upload_dir, exist_ok=True)
                    file_path = os.path.join(upload_dir, filename)
                    
                    with open(file_path, 'wb') as f:
                        f.write(uploaded_file)
                        
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    system_msg = f"\n[{timestamp}] [System Event]: Денис прикрепил документ: {filename} (сохранен в {file_path}). Агенты, проанализируйте этот документ и ответьте Денису!\n"
                    with open(CHAT_FILE, 'a', encoding='utf-8') as f:
                        f.write(system_msg)
                    WAKE_EVENT.set() # Wake up the main loop instantly!
                        
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success", "message": f"Файл {filename} успешно прикреплен!"}).encode('utf-8'))
                    return
                else:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "Файл не найден в запросе."}).encode('utf-8'))
                    return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": f"Ошибка загрузки: {e}"}).encode('utf-8'))
                return

        post_data = self.rfile.read(content_length).decode('utf-8')
        try:
            params = json.loads(post_data) if post_data else {}
        except Exception:
            params = {}
            
        if self.path == '/api/control':
            action = params.get('action')
            res = handle_system_action(action)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
        elif self.path == '/api/command':
            cmd = params.get('command')
            res = handle_send_command(cmd)
            json_response(self, res)
        elif self.path.startswith('/api/panel/'):
            import urllib.request
            target_path = self.path.replace('/api/panel/', '/', 1)
            target_url = f"http://localhost:8000{target_path}"
            try:
                req = urllib.request.Request(target_url, data=post_data.encode('utf-8') if post_data else None,
                    headers={'Content-Type': content_type} if content_type else {})
                proxy_resp = urllib.request.urlopen(req, timeout=10)
                content = proxy_resp.read()
                self.send_response(proxy_resp.status)
                self.send_header('Content-Type', proxy_resp.headers.get('Content-Type', 'application/json'))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Proxy error: {e}"}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def start_dashboard_server():
    import threading
    start_syncthing_poller()
    port = int(os.environ.get("GMC_DASHBOARD_PORT", "8080"))
    try:
        server = ThreadingHTTPServer(('0.0.0.0', port), DashboardHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        print(f"🖥️ Интерактивная веб-панель запущена на http://0.0.0.0:{port}")
    except Exception as e:
        print(f"⚠️ Не удалось запустить веб-панель на порту {port}: {e}")

        time.sleep(10) # Ждем загрузки

def run_agent():
    if not acquire_singleton_lock():
        return

    # Проверяем ресурсы перед стартом
    check_and_start_ollama()
    control = apply_agent_control()
    
    print(f"🚀 Агент [{DEVICE_NAME}] запущен (Dual Mode: Ollama/Gemini)...")
    print(f"🎛 Режим: {control.get('mode')}; команды: {COMMAND_FILE}")
    
    # Запускаем интерактивную веб-панель управления
    start_dashboard_server()

    if not os.path.exists(LIVE_CHAT_FILE) and os.path.exists(CHAT_FILE):
        try:
            import shutil
            shutil.copy2(CHAT_FILE, LIVE_CHAT_FILE)
        except Exception:
            pass

    if os.environ.get("GMC_START_HEARTBEAT", "").lower() in ("1", "true", "yes", "on"):
        heartbeat_path = os.path.join(BASE_DIR, 'heartbeat.py')
        log_path = os.path.join(BASE_DIR, 'heartbeat.log')
        try:
            log_file = open(log_path, 'a', encoding='utf-8')
            # Запускаем Heartbeat абсолютно скрыто и перенаправляем вывод в heartbeat.log
            subprocess.Popen(
                ['python', '-u', heartbeat_path],
                stdout=log_file,
                stderr=log_file,
                creationflags=0x08000000 # CREATE_NO_WINDOW
            )
            print(f"🫀 Heartbeat Daemon запущен в фоновом режиме. Логи: {log_path}")
        except Exception as e:
            print(f"❌ Ошибка запуска Heartbeat: {e}")
    else:
        print("🫀 Heartbeat Daemon не запускается автоматически. Для включения установите GMC_START_HEARTBEAT=1.")

    pending_cmd_offset = None
    while True:
        manual_command, pending_cmd_offset = read_manual_command()
        triage_reply = None
        if manual_command:
            lines = [f"[Manual Command]: {manual_command}\n"]
            last_line = f"[Manual Command]: {manual_command}"
            last_sender = "denis"

            is_slash_cmd = manual_command.strip().startswith("/")
            if is_slash_cmd:
                triage_reply = None
            else:
                print("[Gemma Triage] Запуск мгновенного локального диспетчера для рулевого управления...")
                triage_prompt = (
                    f"Ты — Диспетчер-Аналитик Gemma Triage Officer. Денис ввёл: '{manual_command}'.\n"
                    f"Твоя задача за 1-2 предложения:\n"
                    f"1. Классифицируй запрос: (задача / вопрос / команда / файл)\n"
                    f"2. Выдели ключевые сущности (даты, имена, суммы)\n"
                    f"3. Сформулируй steering context для тяжелой модели (DeepSeek): что именно искать, на чём фокусироваться\n"
                    f"Начни ответ со '[Gemma Triage Officer]: '. На русском.\n"
                    f"Пример: '[Gemma Triage Officer]: Классифицировано как запрос по задаче. Ключевые сущности: договор №123, срок 01.06. Фокус: проверить статус подписания.'"
                )
                triage_reply = query_local_ollama(triage_prompt, model="gemma3:latest")
                if not triage_reply:
                    triage_reply = f"[Gemma Triage Officer]: Принято! Направляю тяжелую модель на глубокий анализ вашего запроса: '{manual_command}'."

                t_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                with open(CHAT_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"\n[{t_timestamp}] [Gemma Triage Officer]: {triage_reply}\n")
                print(f"[Gemma Triage] Ответ записан: {triage_reply}")
        else:
            chat_path = active_chat_path()
            if not os.path.exists(chat_path):
                time.sleep(10); continue

            trim_chat_file_if_needed()
            with CHAT_IO_LOCK:
                with open(chat_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

            if not lines:
                time.sleep(10); continue

            last_line, last_sender = find_actionable_chat_line(lines)
            if not last_line:
                time.sleep(10); continue
            
        print(f"[{DEVICE_NAME}] Анализирую входящее сообщение...")
        
        reply = ""
        control_reply = handle_control_command(last_line)
        
        # ──────────────────────────────────────────────────────────────────────
        # Ветвь 1: Запуск скрипта
        # ──────────────────────────────────────────────────────────────────────
        if control_reply:
            reply = control_reply
        elif manual_command and not manual_command.strip().startswith("/") and len(manual_command) < 400:
            print("[Brain Routing] Быстрый ответ Gemma на команду из панели...")
            reply = query_local_ollama(
                f"Денис написал: «{manual_command}»\n"
                f"Ответь по-русски, 1–3 предложения, конкретно и по делу."
            )
            if not reply:
                reply = f"Принял: «{manual_command}». Обрабатываю (локальная модель временно недоступна)."
        elif "!run" in last_line.lower():
            after_run = last_line.split("!run")[-1].strip()
            import shlex
            try:
                args = shlex.split(after_run)
            except Exception:
                args = after_run.split()
            
            if args:
                script_name = args[0].rstrip(',.')
                script_args = args[1:]
                script_path = os.path.join(BASE_DIR, script_name)
                if os.path.exists(script_path):
                    py = "py" if os.name == 'nt' else "python3"
                    res = subprocess.run([py, script_path] + script_args, capture_output=True, text=True)
                    if res.returncode == 0:
                        reply = res.stdout.strip() or "Выполнено."
                    else:
                        err = res.stderr.strip() or res.stdout.strip() or "Неизвестная ошибка выполнения скрипта."
                        register_complaint(f"!run {script_name}", err)
                        reply = f"[WhatsApp Reply]: ⚠️ [ИИ Ошибка на {DEVICE_NAME}]: Не удалось запустить скрипт {script_name}. Жалоба добавлена в AGENTS_COMPLAINTS.md. Antigravity, пожалуйста, помоги починить!\n\nДетали ошибки:\n{err}"
                else:
                    reply = f"Файл {script_name} не найден."
            else:
                reply = "Укажите имя скрипта для запуска."
        
        # ──────────────────────────────────────────────────────────────────────
        # Ветвь 2: Запрос погоды
        # ──────────────────────────────────────────────────────────────────────
        elif "!taskadd" in last_line.lower():
            try:
                import task_manager
                text = last_line.split("!taskadd")[-1].strip().lstrip(": ").lstrip(",")
                if text:
                    t = task_manager.add(text)
                    reply = f"✅ Задача добавлена: [{t['id']}] {t['text']}"
                else:
                    reply = "Укажи текст задачи после !taskadd:"
            except Exception as e:
                reply = f"Ошибка добавления задачи: {e}"
            
        elif "!погода" in last_line.lower():
            reply = f"Погода: {get_weather()}"
            
        # ──────────────────────────────────────────────────────────────────────
        # Ветвь 3: Запрос к Google API
        # ──────────────────────────────────────────────────────────────────────
        elif "!google" in last_line.lower():
            print(f"Выполняю запрос к Google API...")
            try:
                after_google = last_line.split("!google")[-1].strip()
                import shlex
                try:
                    g_args = shlex.split(after_google)
                except Exception:
                    g_args = after_google.split()
                
                service = g_args[0].lower() if len(g_args) > 0 else "calendar"
                import google_tool
                
                if "calendar" in service:
                    reply = google_tool.list_calendar()
                elif "drive" in service:
                    reply = google_tool.list_drive()
                elif "mail" in service or "gmail" in service:
                    query = g_args[1] if len(g_args) > 1 else "is:unread"
                    reply = google_tool.search_gmail(query)
                elif "photo" in service:
                    reply = google_tool.list_photos()
                elif "tasks" in service or "tasklist" in service:
                    reply = google_tool.list_tasks()
                elif "task" in service:
                    title = g_args[1] if len(g_args) > 1 else "Новая задача"
                    notes = g_args[2] if len(g_args) > 2 else None
                    reply = google_tool.add_task(title, notes)
                elif "draft" in service:
                    # !google draft "subject" "to" "body"
                    subject = g_args[1] if len(g_args) > 1 else "Черновик"
                    to_email = g_args[2] if len(g_args) > 2 else "denisvalerievichmayorov1@gmail.com"
                    body = g_args[3] if len(g_args) > 3 else "Текст черновика"
                    reply = google_tool.create_gmail_draft(subject, to_email, body)
                else:
                    reply = "Доступные сервисы: calendar, drive, mail, photo, tasks, task, draft."
                
                if ("ошибка" in reply.lower() or "error" in reply.lower() or "not authorized" in reply.lower()) and "сохранен локально" not in reply.lower():
                    register_complaint(f"!google {service}", reply)
                    reply = f"[WhatsApp Reply]: ⚠️ [ИИ Ошибка на {DEVICE_NAME}]: Сбой при обращении к Google {service}. Подробности записаны в AGENTS_COMPLAINTS.md. Antigravity, помоги!"
            except Exception as e:
                err = str(e)
                register_complaint("!google command execution", err)
                reply = f"[WhatsApp Reply]: ⚠️ [ИИ Ошибка на {DEVICE_NAME}]: Сбой выполнения google-команды. Жалоба записана в AGENTS_COMPLAINTS.md. Antigravity, помоги!\n\nОшибка:\n{err}"
            
        # ──────────────────────────────────────────────────────────────────────
        # Ветвь 4: Обычная беседа (Поддержка диалога и отчетов)
        # ──────────────────────────────────────────────────────────────────────
        else:
            # --- Защита от бесконечного цикла ошибок ---
            if any(indicator in last_line for indicator in ["⚠️", "Ошибка", "Сбой", "Antigravity", "жалоба", "complaint"]):
                print("Loop protection: Last line is an error or system complaint. Skipping execution.")
                time.sleep(30)
                continue

            # --- Защита от само-диалога: пропускаем собственные мысли агентов ---
            if any(tag in last_line for tag in ["[GMC Proactive Brain]", "[Gemma Triage Officer]"]):
                print("Loop protection: Skipping own agent message.")
                time.sleep(10)
                continue

            context = "".join(lines[-5:])
            is_event = "[System Event]" in last_line
            
            # Поиск упоминания медиа-файла
            image_path = None
            if "[media:" in last_line.lower():
                try:
                    filename = last_line.split("[Media: ")[1].split("]")[0]
                    full_path = os.path.join(BASE_DIR, 'whatsapp_media', filename)
                    if os.path.exists(full_path):
                        image_path = full_path
                except Exception: pass

            # Подгружаем историю переписки в WhatsApp для полного контекста
            wa_context = ""
            if "whatsapp" in last_line.lower():
                wa_file = os.path.join(BASE_DIR, 'whatsapp_messages.txt')
                if os.path.exists(wa_file):
                    try:
                        with open(wa_file, 'r', encoding='utf-8') as waf:
                            wa_context = "".join(waf.readlines()[-15:])
                    except Exception: pass

            # Настраиваем проактивную роль агента в зависимости от типа события
            if "whatsapp от дениса:" in last_line.lower():
                role = (
                    "Денис написал тебе лично в WhatsApp. Твой ответ обязательно ДОЛЖЕН начинаться строго с '[WhatsApp Reply]: '. "
                    "Прояви инициативу: не спрашивай разрешения и не задавай вопросов 'что делать?'. Если в запросе Дениса есть задача "
                    "(проверить почту, календарь, файлы, запустить скрипт, обновить километраж), СНАЧАЛА самостоятельно выполни её с помощью !run or !google, "
                    "а затем отчитайся о полностью выполненной работе. "
                    "⚠️ КРИТИЧЕСКОЕ ПРАВИЛО: Тебе категорически ЗАПРЕЩЕНО самостоятельно отправлять письма (send/reply email) или писать сообщения другим контактам в WhatsApp без прямого и явного согласия Дениса. Все остальные автономные действия (чтение почты, генерация отчетов, вычисления) полностью разрешены!"
                )
                prompt = f"Ты ИИ Дениса. {role}\n\nИстория переписки в WhatsApp для контекста:\n{wa_context}\n\nТекущий чат-рум:\n{context}"
            elif "новое сообщение в whatsapp:" in last_line.lower():
                role = (
                    "В WhatsApp пришло новое сообщение от другого контакта. Проанализируй его в контексте всей переписки. "
                    "Прояви инициативу: если сообщение требует внимания Дениса (электротехника, сын Антон, важные планы), "
                    "самостоятельно подготовь нужную информацию, проверь календарь или документы через !google/!run, "
                    "и составь краткое проактивное уведомление для Дениса. Оно ДОЛЖНО начинаться строго с '[WhatsApp Reply]: [ИИ Уведомление]: '. "
                    "⚠️ КРИТИЧЕСКОЕ ПРАВИЛО: Тебе категорически ЗАПРЕЩЕНО самостоятельно отправлять письма или писать сообщения другим контактам в WhatsApp без прямого и явного согласия Дениса."
                )
                prompt = f"Ты ИИ Дениса. {role}\n\nИстория переписки в WhatsApp для контекста:\n{wa_context}\n\nТекущий чат-рум:\n{context}"
            else:
                role = (
                    "Ты проактивный ИИ Дениса. Возьми инициативу на себя! Не задавай вопросов Денису и не переспрашивай 'что делать?'. "
                    "Если видишь задачу, новость или событие — самостоятельно выполни необходимые действия с помощью !google или !run, "
                    "а затем просто кратко отчитайся о завершенной работе. "
                    "⚠️ КРИТИЧЕСКОЕ ПРАВИЛО: Тебе категорически ЗАПРЕЩЕНО самостоятельно отправлять письма или писать сообщения другим контактам в WhatsApp без прямого и явного согласия Дениса. Все остальные действия (чтение писем, планирование, расчеты, генерация отчетов) разрешены и поощряются!"
                ) if is_event else "Ответь кратко по существу, отчитываясь о проделанной работе, без лишних вопросов."
                prompt = f"Ты ИИ Дениса. {role} Чат:\n{context}"

            control = apply_agent_control()
            extra_instruction = control.get("system_instruction", "").strip()
            if extra_instruction:
                prompt = f"{prompt}\n\nПостоянная пользовательская инструкция Дениса:\n{extra_instruction}"
            
            if manual_command and triage_reply:
                prompt = (
                    f"{prompt}\n\n"
                    f"⚠️ РУЛЕВОЕ УКАЗАНИЕ ОТ ДИСПЕТЧЕРА GEMMA:\n"
                    f"Следуй направлению: {triage_reply}\n"
                    f"Сфокусируй свой детальный ответ именно на выполнении этой инструкции Дениса."
                )
            
            # --- Маршрутизация: local=Gemma; hybrid=Gemma быстро + DeepSeek на сложные; heavy=DeepSeek ---
            reply = None
            control_mode = load_agent_control().get("mode", "local")
            need_deep = (
                is_event or len(prompt) > 400
                or "!google" in prompt.lower() or "!run" in prompt.lower()
                or bool(manual_command)
            )
            if not image_path:
                if control_mode == "heavy":
                    print("[Brain Routing] Heavy: DeepSeek → Gemma fallback...")
                    reply = query_openrouter_api(prompt)
                    if not reply:
                        reply = query_local_ollama(prompt)
                elif control_mode == "hybrid":
                    print("[Brain Routing] Hybrid: Gemma (локально)...")
                    reply = query_local_ollama(prompt)
                    if need_deep and OPENROUTER_ENABLED:
                        print("[Brain Routing] Hybrid: сложный запрос → DeepSeek...")
                        deep = query_openrouter_api(prompt)
                        if deep:
                            reply = deep
                    elif not reply and OPENROUTER_ENABLED:
                        reply = query_openrouter_api(prompt)
                else:
                    print("[Brain Routing] Local: только Gemma/Ollama...")
                    reply = query_local_ollama(prompt)
                        
            if not reply:
                print("[Gemini] Обращаюсь к облачному Gemini (локальные модели недоступны или требуется зрение)...")
                try:
                    cmd = get_cli_command()
                    env = os.environ.copy()
                    env['GEMINI_CLI_TRUST_WORKSPACE'] = 'true'
                    if os.name != 'nt': env['GEMINI_API_KEY'] = 'AIzaSyAZDjMC3VsfelEaYUvprKqFBRs9xyOggYg'
                    
                    args = [cmd, "--skip-trust", "-o", "text", "--yolo", "-p", prompt]
                    if image_path:
                        args.extend(["-i", image_path])
                    
                    result = subprocess.run(args, capture_output=True, text=True, env=env, timeout=90)
                    
                    if result.returncode == 0:
                        reply = result.stdout.strip().replace('**', '')
                    else:
                        error_msg = result.stderr.strip() or "Неизвестная ошибка Gemini CLI."
                        register_complaint("Gemini CLI execution", error_msg)
                        
                        log_file = os.path.join(BASE_DIR, 'agent.log')
                        with open(log_file, 'a', encoding='utf-8') as lf:
                            lf.write(f"[{datetime.datetime.now().isoformat()}] Error running gemini CLI: {error_msg}\n")
                        
                        if "auth" in error_msg.lower() or "login" in error_msg.lower():
                            reply = f"[WhatsApp Reply]: ⚠️ [ИИ Ошибка на {DEVICE_NAME}]: Ошибка авторизации Gemini подписки. Требуется 'gemini --login'. Antigravity, помоги!"
                        else:
                            reply = f"[WhatsApp Reply]: ⚠️ [ИИ Ошибка на {DEVICE_NAME}]: Сбой Gemini CLI. Подробности записаны в AGENTS_COMPLAINTS.md. Antigravity, помоги!"
                except Exception as e:
                    err = str(e)
                    register_complaint("agent_listener runtime exception", err)
                    log_file = os.path.join(BASE_DIR, 'agent.log')
                    with open(log_file, 'a', encoding='utf-8') as lf:
                        lf.write(f"[{datetime.datetime.now().isoformat()}] Exception in run_agent: {err}\n")
                    reply = f"[WhatsApp Reply]: ⚠️ [ИИ Критическая ошибка на {DEVICE_NAME}]: Исключение в рантайме слушателя. Подробности в AGENTS_COMPLAINTS.md. Antigravity, помоги!"
                
        if reply:
            reply = reply.strip()
            
            # Если это был WhatsApp запрос от Дениса, принудительно гарантируем наличие префикса [WhatsApp Reply]:
            if "whatsapp от дениса:" in last_line.lower():
                if not reply.startswith("[WhatsApp Reply]:"):
                    clean_reply = reply
                    if reply.startswith(f"[{DEVICE_NAME}]:"):
                        clean_reply = reply.split(f"[{DEVICE_NAME}]:")[-1].strip()
                    reply = f"[WhatsApp Reply]: {clean_reply}"
            
            # --- Улучшенная дедупликация и защита от "тенниса" ---
            if not reply or (len(reply) < 5 and not reply.startswith("!")):
                print("Reply too short, skipping.")
                time.sleep(15)
                continue

            stop_phrases = [
                "принято. ожидаю новых инструкций.",
                "принято. ожидаю инструкций.",
                "ожидаю новых инструкций.",
                "ожидаю инструкций.",
                "я готов к работе.",
                "чем я могу помочь?",
                "готов к выполнению задач.",
                "принято. на связи."
            ]
            
            reply_lower = reply.lower().rstrip('.')
            is_stop_phrase = any(phrase.rstrip('.') in reply_lower for phrase in stop_phrases)
            
            recent_lines = [l.strip().lower() for l in lines[-10:]] if lines else []
            
            if is_stop_phrase:
                if any(phrase.rstrip('.') in msg for msg in recent_lines for phrase in stop_phrases):
                    print(f"Loop protection: Generic phrase already in history. Silent mode.")
                    time.sleep(30)
                    continue
            
            reply_snippet = reply.lower()[:120]
            if reply_snippet and any(reply_snippet in msg for msg in recent_lines if len(msg) > 40):
                print(f"Duplicate content detected in recent history, skipping.")
                time.sleep(20)
                continue

            safe_reply = reply.replace("\r\n", "\n").strip()
            append_chat_line(DEVICE_NAME, safe_reply)
            print("Отправлено:", reply[:120])
            if pending_cmd_offset is not None:
                commit_manual_command_offset(pending_cmd_offset)
                pending_cmd_offset = None
            time.sleep(10)  # пауза после ответа, чтобы не читать свой же вывод
        
        # Widescreen & mobile instant wakeup trigger
        WAKE_EVENT.wait(timeout=15 if not manual_command else 5)
        WAKE_EVENT.clear()

if __name__ == '__main__':
    run_agent()
