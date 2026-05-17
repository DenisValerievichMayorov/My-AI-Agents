import os
import subprocess
import socket
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEVICE_NAME = socket.gethostname().lower()

def is_android():
    return 'motorola' in DEVICE_NAME or os.name != 'nt' and 'penguin' not in DEVICE_NAME

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

def check_mail():
    """Проверяет почту на новые непрочитанные сообщения с кэшированием на 45 секунд."""
    global _last_mail_check, _cached_mail_events
    now_ts = datetime.datetime.now().timestamp()
    if now_ts - _last_mail_check < 45:
        return _cached_mail_events
        
    _last_mail_check = now_ts
    _cached_mail_events = []
    
    # 1. Проверяем новые непрочитанные через Gmail API (google_tool)
    try:
        import google_tool
        creds = google_tool.get_creds()
        if creds:
            from googleapiclient.discovery import build
            service = build('gmail', 'v1', credentials=creds)
            results = service.users().messages().list(userId='me', q='is:unread', maxResults=5).execute()
            messages = results.get('messages', [])
            
            notified_file = os.path.join(BASE_DIR, 'logs', 'notified_emails.txt')
            os.makedirs(os.path.dirname(notified_file), exist_ok=True)
            notified_ids = set()
            if os.path.exists(notified_file):
                with open(notified_file, 'r', encoding='utf-8') as nf:
                    notified_ids = set(line.strip() for line in nf if line.strip())

            new_emails = []
            for m in messages:
                m_id = m['id']
                if m_id not in notified_ids:
                    msg_detail = service.users().messages().get(userId='me', id=m_id).execute()
                    headers = msg_detail.get('payload', {}).get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'Без темы')
                    from_ = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Неизвестный отправитель')
                    
                    new_emails.append(m_id)
                    _cached_mail_events.append({
                        "type": "mail",
                        "content": f"От: {from_} | Тема: {subject}"
                    })
            
            if new_emails:
                with open(notified_file, 'a', encoding='utf-8') as nf:
                    for m_id in new_emails:
                        nf.write(f"{m_id}\n")
    except Exception as e:
        print(f"[sensors] Ошибка проверки Gmail API: {e}")

    # 2. Если Gmail API недоступен, пробуем резервный IMAP поиск писем от ABVV/FGTB
    if not _cached_mail_events:
        script_path = os.path.join(BASE_DIR, 'Legacy', 'get_gmail.py')
        if os.path.exists(script_path) and os.name == 'nt':
            try:
                py = "py" if os.name == 'nt' else "python3"
                result = subprocess.run([py, script_path], capture_output=True, text=True, timeout=20)
                if result.stdout and "Найдено писем:" in result.stdout:
                    count_line = [l for l in result.stdout.split('\n') if "Найдено писем:" in l][0]
                    count = int(count_line.split(":")[-1].strip())
                    if count > 0:
                        subject = "Новое письмо ABVV/FGTB"
                        for line in result.stdout.split('\n'):
                            if "Тема:" in line:
                                subject = line.replace("Тема:", "").strip()
                                break
                        _cached_mail_events = [{"type": "mail", "content": f"ABVV: {subject}"}]
            except Exception:
                pass
                
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

def get_all_events():
    """Собирает все события со всех сенсоров."""
    all_events = []
    all_events.extend(check_sync())
    all_events.extend(check_mail())
    all_events.extend(check_photos())
    all_events.extend(check_whatsapp())
    return all_events
