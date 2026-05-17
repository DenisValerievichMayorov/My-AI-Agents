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

def check_mail():
    """Проверяет почту и возвращает заголовки новых писем (только на ПК)."""
    script_path = os.path.join(BASE_DIR, 'Legacy', 'get_gmail.py')
    if os.path.exists(script_path) and os.name == 'nt':
        try:
            # Используем абсолютный путь к python
            py = "py" if os.name == 'nt' else "python3"
            result = subprocess.run([py, script_path], capture_output=True, text=True, timeout=30)
            if result.stdout and "Найдено писем:" in result.stdout:
                count_line = [l for l in result.stdout.split('\n') if "Найдено писем:" in l][0]
                count = int(count_line.split(":")[-1].strip())
                if count > 0:
                    # Парсим заголовок (упрощенно)
                    subject = "Новое письмо"
                    for line in result.stdout.split('\n'):
                        if "Тема:" in line:
                            subject = line.replace("Тема:", "").strip()
                            break
                    return [{"type": "mail", "content": subject}]
        except Exception:
            pass
    return []

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
