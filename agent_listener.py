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
    print(f"⚠️ Жалоба на '{action}' успешно зарегистрирована in AGENTS_COMPLAINTS.md")

def get_weather():
    try:
        req = urllib.request.Request("https://wttr.in/Antwerp?format=3", headers={'User-Agent': 'curl/7.68.0'})
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8').strip()
    except Exception: return "Нет данных о погоде."

def query_local_ollama(prompt):
    """Отправляет запрос в локальную модель Ollama (предпочитая Gemma), если она запущена."""
    import urllib.request
    import json
    
    # Список хостов для проверки:
    # Если мы не на главном ПК (DESKTOP-85D3NJI), пробуем сначала достучаться до ПК по Tailscale IP
    hosts = ["http://localhost:11434"]
    if "desktop" not in DEVICE_NAME.lower():
        hosts.insert(0, "http://100.72.214.118:11434") # Tailscale IP главного Windows ПК
        
    for host in hosts:
        try:
            # 1. Проверяем доступность API и список моделей
            req = urllib.request.urlopen(f"{host}/api/tags", timeout=2)
            data = json.loads(req.read().decode())
            models = [m['name'] for m in data.get('models', [])]
            if not models:
                continue
                
            # 2. Выбираем лучшую модель из доступных (предпочитаем gemma)
            selected_model = None
            for preferred in ["gemma2:2b", "gemma2", "gemma", "llama3.2", "qwen2.5-coder", "llama3"]:
                for m in models:
                    if m.lower().startswith(preferred):
                        selected_model = m
                        break
                if selected_model:
                    break
            
            if not selected_model:
                selected_model = models[0] # берем первую попавшуюся
                
            print(f"[Ollama] Использую модель: {selected_model} на хосте {host}")
            
            # 3. Делаем запрос к /api/generate
            payload = {
                "model": selected_model,
                "prompt": prompt,
                "stream": False
            }
            
            req_post = urllib.request.Request(
                f"{host}/api/generate",
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req_post, timeout=30) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                return res_data.get('response', '').strip()
                
        except Exception as e:
            print(f"[Ollama] Хост {host} недоступен или произошла ошибка: {e}")
            
    return None

def query_openrouter_api(prompt):
    """Отправляет запрос к OpenRouter API с поддержкой Nemotron/Llama 70B (Hermes API)."""
    import json
    import urllib.request
    
    # Пытаемся импортировать ключ
    try:
        import reasoning_engine
        api_key = reasoning_engine.load_openrouter_key()
    except Exception:
        api_key = None
        
    if not api_key:
        return None
        
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/antigravity/gmc",
        "X-Title": "GMC Listener Brain"
    }
    
    # Список бесплатных моделей высокой производительности на OpenRouter
    models_to_try = [
        "nvidia/nemotron-3-super-120b-a12b:free",
        "google/gemma-4-31b-it:free",
        "deepseek/deepseek-v4-flash:free",
        "poolside/laguna-m.1:free"
    ]
    
    for selected_model in models_to_try:
        system_prompt = (
            "Ты — высокопроизводительный ИИ-советник Дениса (Nemotron-120B Brain). Ты помогаешь ему в повседневных делах, электротехнике и автоматизации.\n"
            "⚠️ КРИТИЧЕСКОЕ ПРАВИЛО 1: Каждый твой ответ ОБЯЗАТЕЛЬНО должен содержать две четкие секции:\n"
            "1. 💭 **Ход мыслей:** (Твой пошаговый внутренний мыслительный процесс: анализ контекста, разбор текущих задач Дениса, оценка того, что нужно сделать или какие локальные файлы проверить, и твои логические выводы).\n"
            "2. 👉 **Решение:** (Твой итоговый практический ответ Денису).\n"
            "⚠️ КРИТИЧЕСКОЕ ПРАВИЛО 2: Тебе КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать пустые обещания о действиях в будущем времени (например, 'тест будет запущен', 'сейчас очистим'). Вместо слов ты должен РЕАЛЬНО ЗАПУСКАТЬ действия, вставляя команду `!run <имя_скрипта>` прямо в секцию 👉 **Решение:**!\n"
            "Тебе доступны следующие скрипты на компьютере:\n"
            "- `cleaner.py` (полная очистка ОЗУ от зомби-процессов Chrome и удаление мусора Syncthing).\n"
            "- `test_dependencies.py` (запуск интеграционных тестов и проверка целостности библиотек системы).\n"
            "- `sensors.py` (проверка статуса системы, батареи и системная диагностика).\n"
            "- `google_tool.py` (работа с Google Calendar и Gmail).\n"
            "- `generate_pdf_report.py` (генерация PDF-отчета о поездках).\n"
            "Пример: если нужно проверить библиотеки или запустить тест, напиши в решении: 'Запускаю интеграционный тест: !run test_dependencies.py'.\n"
            "Отвечай на чистом русском языке, профессионально и уверенно."
        )
        payload = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                choices = res_data.get('choices', [])
                if choices:
                    content = choices[0].get('message', {}).get('content', '').strip()
                    if content:
                        print(f"[OpenRouter] Успешный ответ от модели {selected_model}")
                        return content
        except Exception as e:
            print(f"[OpenRouter] Ошибка {selected_model}: {e}")
    return None

def run_agent():
    print(f"🚀 Агент [{DEVICE_NAME}] запущен (Dual Mode: Ollama/Gemini)...")
    
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
            
        # Находим последнюю непустую строку для парсинга команд
        last_line = ""
        for line in reversed(lines):
            if line.strip():
                last_line = line.strip()
                break
                
        if not last_line:
            time.sleep(5); continue
            
        # Ищем отправителя последнего сообщения снизу вверх для надежной защиты от мультистрочных петель
        last_sender = None
        for line in reversed(lines):
            line_str = line.strip()
            if line_str.startswith("[") and "]:" in line_str:
                last_sender = line_str.split("]:", 1)[0] + "]:"
                break
                
        if last_sender:
            clean_sender = last_sender.strip("[]: ").lower()
            # Если отправитель — другой ИИ-агент (не Денис, не WhatsApp и не системное оповещение),
            # мы полностью игнорируем сообщение, чтобы исключить пинг-понг теннис между устройствами.
            if "denis" not in clean_sender and "денис" not in clean_sender and "system alert" not in clean_sender:
                time.sleep(5); continue
            
        print(f"[{DEVICE_NAME}] Анализирую входящее сообщение...")
        
        reply = ""
        
        # ──────────────────────────────────────────────────────────────────────
        # Ветвь 1: Запуск скрипта
        # ──────────────────────────────────────────────────────────────────────
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
        
        # ──────────────────────────────────────────────────────────────────────
        # Ветвь 2: Запрос погоды
        # ──────────────────────────────────────────────────────────────────────
        elif "!погода" in last_line.lower():
            reply = f"Погода: {get_weather()}"
            
        # ──────────────────────────────────────────────────────────────────────
        # Ветвь 3: Запрос к Google API
        # ──────────────────────────────────────────────────────────────────────
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
                
                if "ошибка" in reply.lower() or "error" in reply.lower() or "not authorized" in reply.lower():
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
            
            # --- Умная маршрутизация: OpenRouter (Nemotron-120B) vs локальный Ollama vs облачный Gemini ---
            reply = None
            if not image_path:
                print("[Brain Routing] Пробую получить ответ от высокопроизводительного OpenRouter (Nemotron-120B)...")
                reply = query_openrouter_api(prompt)
                if reply:
                    print("[OpenRouter] Успешный ответ от Nemotron-120B получен!")
                else:
                    print("[Brain Routing] OpenRouter недоступен. Пробую локальный Ollama...")
                    reply = query_local_ollama(prompt)
                    if reply:
                        print("[Ollama] Локальный ответ от Gemma получен успешно!")
                        
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
                    
                    result = subprocess.run(args, capture_output=True, text=True, env=env)
                    
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
