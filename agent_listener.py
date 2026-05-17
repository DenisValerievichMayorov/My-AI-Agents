import os
import time
import subprocess
import socket
import urllib.request
import datetime

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
    print(f"⚠️ Жалоба на '{action}' успешно зарегистрирована в AGENTS_COMPLAINTS.md")

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
        if last_line.startswith(f"[{DEVICE_NAME}]:"):
            time.sleep(10); continue
            
        print(f"[{DEVICE_NAME}] Думаю через Gemini CLI (Subscription)...")
        
        reply = ""
        if "!run" in last_line.lower():
            after_run = last_line.lower().split("!run")[-1].strip()
            script_name = after_run.split()[0].rstrip(',.') if after_run.split() else ""
            script_path = os.path.join(BASE_DIR, script_name)
            if os.path.exists(script_path):
                py = "py" if os.name == 'nt' else "python3"
                res = subprocess.run([py, script_path], capture_output=True, text=True)
                if res.returncode == 0:
                    reply = res.stdout.strip() or "Выполнено."
                else:
                    err = res.stderr.strip() or res.stdout.strip() or "Неизвестная ошибка выполнения скрипта."
                    register_complaint(f"!run {script_name}", err)
                    reply = f"[WhatsApp Reply]: ⚠️ [ИИ Ошибка на {DEVICE_NAME}]: Не удалось запустить скрипт {script_name}. Жалоба добавлена в AGENTS_COMPLAINTS.md. Antigravity, пожалуйста, помоги починить!\n\nДетали ошибки:\n{err}"
            else:
                reply = f"Файл {script_name} не найден."
        
        elif "!погода" in last_line.lower():
            reply = f"Погода: {get_weather()}"
            
        elif "!google" in last_line.lower():
            print(f"Выполняю запрос к Google API...")
            try:
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
                
                # Если в ответе содержится признак ошибки от самого API
                if "ошибка" in reply.lower() or "error" in reply.lower() or "not authorized" in reply.lower():
                    register_complaint(f"!google {service}", reply)
                    reply = f"[WhatsApp Reply]: ⚠️ [ИИ Ошибка на {DEVICE_NAME}]: Сбой при обращении к Google {service}. Подробности записаны в AGENTS_COMPLAINTS.md. Antigravity, помоги!"
            except Exception as e:
                err = str(e)
                register_complaint("!google command execution", err)
                reply = f"[WhatsApp Reply]: ⚠️ [ИИ Ошибка на {DEVICE_NAME}]: Сбой выполнения google-команды. Жалоба записана в AGENTS_COMPLAINTS.md. Antigravity, помоги!\n\nОшибка:\n{err}"
            
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
                    "(проверить почту, календарь, файлы, запустить скрипт, обновить километраж), СНАЧАЛА самостоятельно выполни её с помощью !run или !google, "
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
            
            try:
                cmd = get_cli_command()
                env = os.environ.copy()
                env['GEMINI_CLI_TRUST_WORKSPACE'] = 'true'
                if os.name != 'nt': env['GEMINI_API_KEY'] = 'AIzaSyAZDjMC3VsfelEaYUvprKqFBRs9xyOggYg'
                
                args = [cmd, "--skip-trust", "-o", "text", "--yolo", "-p", prompt]
                if image_path:
                    args.extend(["-i", image_path])
                
                result = subprocess.run(args, capture_output=True, text=True, env=env)
                
                if result.returncode == 0:
                    reply = result.stdout.strip().replace('**', '')
                else:
                    error_msg = result.stderr.strip() or "Неизвестная ошибка Gemini CLI."
                    register_complaint("Gemini CLI execution", error_msg)
                    
                    # Log error to agent.log
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
                # Log exception
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
            
            if any(reply.lower() in msg for msg in recent_lines):
                print(f"Duplicate content detected in recent history, skipping.")
                time.sleep(20)
                continue
            
            new_msg = f"[{DEVICE_NAME}]: {reply}\n"
            with open(CHAT_FILE, 'a', encoding='utf-8') as f:
                f.write(new_msg)
            print("Отправлено:", reply)
        
        time.sleep(15)

if __name__ == '__main__':
    run_agent()
