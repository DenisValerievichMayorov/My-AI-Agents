import os
import time
import subprocess
import socket
import urllib.request

# Настройки
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAT_FILE = os.path.join(BASE_DIR, 'ai_chat_room.txt')

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

def get_weather():
    try:
        req = urllib.request.Request("https://wttr.in/Antwerp?format=3", headers={'User-Agent': 'curl/7.68.0'})
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8').strip()
    except Exception: return "Нет данных о погоде."

def run_agent():
    print(f"🚀 Агент [{DEVICE_NAME}] запущен (Subscription Mode)...")
    
    while True:
        if not os.path.exists(CHAT_FILE):
            time.sleep(5); continue
            
        with open(CHAT_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if len(lines) > 50:
            with open(CHAT_FILE, 'w', encoding='utf-8') as f:
                f.writelines(lines[-15:])
            continue
            
        if not lines:
            time.sleep(5); continue
            
        last_line = lines[-1].strip()
        if f"[{DEVICE_NAME}]" in last_line:
            time.sleep(10); continue
            
        print(f"[{DEVICE_NAME}] Думаю через Gemini CLI (Subscription)...")
        
        reply = ""
        if "!run" in last_line.lower():
            after_run = last_line.lower().split("!run")[-1].strip()
            script_name = after_run.split()[0] if after_run.split() else ""
            script_path = os.path.join(BASE_DIR, script_name)
            if os.path.exists(script_path):
                py = "py" if os.name == 'nt' else "python3"
                res = subprocess.run([py, script_path], capture_output=True, text=True)
                reply = res.stdout.strip() or "Выполнено."
            else: reply = f"Файл {script_name} не найден."
        
        elif "!погода" in last_line.lower():
            reply = f"Погода: {get_weather()}"
            
        elif "!google" in last_line.lower():
            print(f"Выполняю запрос к Google API...")
            parts = last_line.split()
            service = parts[1].lower() if len(parts) > 1 else "calendar"
            import google_tool
            if "calendar" in service:
                reply = google_tool.list_calendar()
            elif "drive" in service:
                reply = google_tool.list_drive()
            elif "mail" in service:
                query = " ".join(parts[2:]) if len(parts) > 2 else "is:unread"
                reply = google_tool.search_gmail(query)
            elif "photo" in service:
                reply = google_tool.list_photos()
            else:
                reply = "Доступные сервисы: calendar, drive, mail, photo."
            
        else:
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

            role = "Ты проактивный ИИ Дениса. Ты МОЖЕШЬ и ДОЛЖЕН использовать инструменты !google (calendar/mail/drive), !погода или !run, если это поможет ответить. Проанализируй данные и предложи действие." if is_event else "Ответь кратко."
            prompt = f"Ты ИИ Дениса. {role} Чат:\n{context}"
            
            try:
                cmd = get_cli_command()
                env = os.environ.copy()
                env['GEMINI_CLI_TRUST_WORKSPACE'] = 'true'
                if os.name != 'nt': env['GEMINI_API_KEY'] = 'AIzaSyAZDjMC3VsfelEaYUvprKqFBRs9xyOggYg'
                
                args = [cmd, "-m", "gemini-1.5-flash-8b", "-p", prompt]
                if image_path:
                    args.extend(["-i", image_path])
                
                result = subprocess.run(args, capture_output=True, text=True, env=env)
                
                if result.returncode == 0:
                    reply = result.stdout.strip().replace('**', '')
                else:
                    error_msg = result.stderr.lower()
                    if "auth" in error_msg or "login" in error_msg:
                        reply = "Ошибка авторизации подписки на ПК. Введите 'gemini --login' в терминале."
                    else:
                        reply = "Принято. Ожидаю новых инструкций."
            except Exception:
                reply = "Принято. Ожидаю новых инструкций."
                
        if reply:
            new_msg = f"[{DEVICE_NAME}]: {reply}\n"
            with open(CHAT_FILE, 'a', encoding='utf-8') as f:
                f.write(new_msg)
            print("Отправлено:", reply)
        
        time.sleep(15)

if __name__ == '__main__':
    run_agent()
