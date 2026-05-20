import os
import subprocess
import socket
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEVICE_NAME = socket.gethostname().lower()
GOOGLE_TASKS_ENABLED = os.environ.get("GMC_GOOGLE_TASKS", "").lower() in ("1", "true", "yes", "on")

def is_android():
    return 'motorola' in DEVICE_NAME or os.name != 'nt' and 'penguin' not in DEVICE_NAME

def log_chat(message):
    """Записывает лог общения с ИИ в файл."""
    log_path = os.path.join(BASE_DIR, '..', 'Logs', 'chat_history.log')
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'a', encoding='utf-8') as f:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")

def check_sync():
    """Проверяет чат. Если есть новые сообщения от других - возвращает событие."""
    chat_file = os.path.join(BASE_DIR, 'ai_chat_room.txt')
    if os.path.exists(chat_file):
        try:
            mtime = os.path.getmtime(chat_file)
            if datetime.datetime.now().timestamp() - mtime < 60:
                with open(chat_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines and f"[{socket.gethostname()}]" not in lines[-1]:
                        return [{"type": "chat", "content": lines[-1].strip()}]
        except Exception: pass
    return []

_last_mail_check = 0
_cached_mail_events = []

def summarize_text(text):
    """Сжимает текст письма с помощью доступного контекста агента."""
    try:
        import reasoning_engine
        prompt = f"Проанализируй это письмо (включая вложения). Выдай структурированный ответ:\n1. **Суть письма**: 1-2 предложения.\n2. **Требуемые действия**: (если есть, иначе 'Нет').\n3. **Черновик ответа**: (если письмо подразумевает ответ, напиши короткий готовый черновик ответа, иначе 'Не требуется').\n\nТекст письма:\n{text}"
        system_prompt = "Ты - личный ассистент Дениса (электрик, живет в Антверпене). Анализируй почту структурированно, готовь черновики ответов и давай подсказки."
        llm_summary = reasoning_engine.query_openrouter(prompt, system_prompt)
        if llm_summary:
            summary = f"Суммаризация (AI): {llm_summary.strip()}"
            try:
                from mem0 import MemoryClient
                import os
                if 'MEM0_API_KEY' not in os.environ:
                    os.environ['MEM0_API_KEY'] = 'm0-FNdckglmWWITMYsm2J4MjQEmuW9zFGD5bmLN3vKp'
                client = MemoryClient()
                client.add(f"Получено новое письмо. Анализ:\n{llm_summary.strip()}", user_id="denis")
            except Exception as mem_err:
                print(f"[sensors] Ошибка сохранения в Mem0: {mem_err}")
        else:
            summary = f"Суммаризация (Auto): {text[:150]}..."
    except Exception as e:
        print(f"[sensors] Ошибка LLM суммаризации: {e}")
        summary = f"Суммаризация (Fallback): {text[:150]}..."

    text_lower = text.lower()
    if 'задача' in text_lower or 'срочно' in text_lower:
        summary = f"[ВАЖНО] {summary}"
    return summary 

import base64
import io

def get_email_content(service, msg_id):
    msg_detail = service.users().messages().get(userId='me', id=msg_id).execute()
    payload = msg_detail.get('payload', {})

    body_text = msg_detail.get('snippet', '') + '\n\n'
    attachments_text = ''

    def parse_parts(parts):
        nonlocal body_text, attachments_text
        for part in parts:
            mimeType = part.get('mimeType', '')
            filename = part.get('filename', '')
            body = part.get('body', {})
            data = body.get('data')
            attachmentId = body.get('attachmentId')

            if 'parts' in part:
                parse_parts(part['parts'])

            if mimeType == 'text/plain' and data and not filename:
                try:
                    text = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                    body_text += text + '\n'
                except:
                    pass
            elif attachmentId and filename:
                try:
                    attach = service.users().messages().attachments().get(userId='me', messageId=msg_id, id=attachmentId).execute()
                    file_data = base64.urlsafe_b64decode(attach['data'])
                    attachments_text += f'\n--- Вложение: {filename} ---\n'

                    if filename.lower().endswith('.pdf'):
                        try:
                            import PyPDF2
                            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
                            extracted = ''
                            for page in pdf_reader.pages[:5]:
                                extracted += page.extract_text() + '\n'
                            attachments_text += extracted[:2000]
                        except Exception as e:
                            attachments_text += f'[Не удалось прочитать PDF: {e}]\n'
                    elif filename.lower().endswith(('.txt', '.csv', '.json', '.md')):
                        attachments_text += file_data.decode('utf-8', errors='replace')[:2000]
                    else:
                        attachments_text += f'[Вложение {filename} (тип: {mimeType}) сохранено, но текст не извлечен]\n'
                except Exception as e:
                    print(f'Ошибка загрузки вложения {filename}: {e}')

    if 'parts' in payload:
        parse_parts(payload['parts'])
    elif payload.get('body', {}).get('data'):
        try:
            body_text += base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
        except:
            pass

    full_text = body_text.strip()
    if attachments_text.strip():
        full_text += '\n' + attachments_text.strip()

    return full_text

def check_mail():
    """Проверяет почту по одному письму за цикл."""
    global _last_mail_check, _cached_mail_events
    now_ts = datetime.datetime.now().timestamp()
    if now_ts - _last_mail_check < 45:
        return _cached_mail_events

    _last_mail_check = now_ts
    _cached_mail_events = []

    try:
        import google_tool
        creds = google_tool.get_creds(['https://www.googleapis.com/auth/gmail.readonly'])
        if creds:
            from googleapiclient.discovery import build
            service = build('gmail', 'v1', credentials=creds)
            # Получаем список всех писем
            results = service.users().messages().list(userId='me', maxResults=50).execute()
            messages = results.get('messages', [])
            # Разворачиваем, чтобы обрабатывать самые старые первыми
            messages.reverse()

            notified_file = os.path.join(BASE_DIR, '..', 'Logs', 'notified_emails.txt')
            os.makedirs(os.path.dirname(notified_file), exist_ok=True)
            notified_ids = set()
            if os.path.exists(notified_file):
                with open(notified_file, 'r', encoding='utf-8') as nf:
                    notified_ids = set(line.strip() for line in nf if line.strip())

            for m in messages:
                m_id = m['id']
                if m_id not in notified_ids:
                    # Обрабатываем только одно письмо за раз
                    body = get_email_content(service, m_id)
                    summary = summarize_text(body)

                    _cached_mail_events.append({
                        "type": "mail",
                        "content": summary
                    })

                    with open(notified_file, 'a', encoding='utf-8') as nf:
                        nf.write(f"{m_id}\n")

                    # Прерываем цикл, чтобы обработать только одно письмо
                    break
    except Exception as e:
        print(f"[sensors] Ошибка проверки Gmail API: {e}")
    return _cached_mail_events
def check_photos():
    """Проверяет новые фото на Android."""
    if not is_android(): return []
    
    paths = [
        "/sdcard/WhatsApp/Media/WhatsApp Images/",
        "/sdcard/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Images/",
        "/sdcard/DCIM/Camera/"
    ]
    
    events = []
    for path in paths:
        if os.path.exists(path):
            try:
                files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(('.jpg', '.png'))]
                if not files: continue
                newest = max(files, key=os.path.getmtime)
                if datetime.datetime.now().timestamp() - os.path.getmtime(newest) < 120: # за последние 2 мин
                    events.append({"type": "photo", "content": newest})
            except Exception: pass
    return events

def check_whatsapp():
    """Проверяет новые сообщения из WhatsApp моста."""
    wa_file = os.path.join(BASE_DIR, 'whatsapp_messages.txt')
    if os.path.exists(wa_file):
        try:
            mtime = os.path.getmtime(wa_file)
            if datetime.datetime.now().timestamp() - mtime < 60:
                with open(wa_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        return [{"type": "whatsapp", "content": lines[-1].strip()}]
        except Exception: pass
    return []

def check_tasks():
    """Проверяет активные задачи в Google Tasks."""
    if not GOOGLE_TASKS_ENABLED:
        return []

    try:
        import google_tool
        creds = google_tool.get_creds(['https://www.googleapis.com/auth/tasks'])
        if creds:
            from googleapiclient.discovery import build
            service = build('tasks', 'v1', credentials=creds)
            # Список всех списков задач
            task_lists = service.tasklists().list().execute().get('taskLists', [])
            tasks_list = []
            for tlist in task_lists:
                tasks = service.tasks().list(tasklist=tlist['id'], showCompleted=False).execute().get('items', [])
                for t in tasks:
                    tasks_list.append(f"{tlist['title']}: {t.get('title', 'Без названия')}")
            return [{"type": "tasks", "content": "; ".join(tasks_list)}] if tasks_list else []
    except Exception as e:
        print(f"[sensors] Ошибка проверки Google Tasks: {e}")
    return []

def get_all_events():
    """Собирает все события со всех сенсоров."""
    all_events = []
    all_events.extend(check_sync())
    all_events.extend(check_mail())
    all_events.extend(check_photos())
    all_events.extend(check_whatsapp())
    if GOOGLE_TASKS_ENABLED:
        all_events.extend(check_tasks())
    return all_events
