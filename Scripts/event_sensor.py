import os
from os import path
import json
import time
import datetime
from google_tool import get_creds
from googleapiclient.discovery import build

SYNC_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SYNC_DIR, 'sensor_state.json')
LOG_FILE = path.join(os.path.dirname(SYNC_DIR), 'sensor_events.log')
WHATSAPP_FILE = path.join(os.path.dirname(SYNC_DIR), 'whatsapp_messages.txt')
AI_CHAT_FILE = path.join(os.path.dirname(SYNC_DIR), 'ai_chat_room.txt')

def log_event(message, notify=False):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")
    
    if notify:
        with open(AI_CHAT_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n[WhatsApp Reply]: [Сенсор]: {message}\n")

def get_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"gmail": [], "tasks": [], "drive": [], "whatsapp_last_line": 0}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def check_gmail(state):
    creds = get_creds(['https://www.googleapis.com/auth/gmail.readonly'])
    if not creds: return
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', maxResults=5).execute()
    messages = results.get('messages', [])
    new_ids = [m['id'] for m in messages]
    
    old_ids = state.get("gmail", [])
    for m_id in new_ids:
        if m_id not in old_ids:
            msg = service.users().messages().get(userId='me', id=m_id).execute()
            subject = next((h['value'] for h in msg['payload']['headers'] if h['name'] == 'Subject'), 'No Subject')
            log_event(f"GMAIL: Новое письмо! Тема: {subject}", notify=True)
    
    state["gmail"] = new_ids

def check_tasks(state):
    creds = get_creds(['https://www.googleapis.com/auth/tasks'])
    if not creds: return
    service = build('tasks', 'v1', credentials=creds)
    results = service.tasks().list(tasklist='@default', maxResults=10, showCompleted=False).execute()
    tasks = results.get('items', [])
    new_ids = [t['id'] for t in tasks]
    
    old_ids = state.get("tasks", [])
    for t_id in new_ids:
        if t_id not in old_ids:
            task = next(t for t in tasks if t['id'] == t_id)
            log_event(f"TASK: Новая задача! {task['title']}", notify=True)
    
    state["tasks"] = new_ids

def check_drive(state):
    creds = get_creds(['https://www.googleapis.com/auth/drive.readonly'])
    if not creds: return
    service = build('drive', 'v3', credentials=creds)
    results = service.files().list(pageSize=5, fields="files(id, name)").execute()
    files = results.get('files', [])
    new_ids = [f['id'] for f in files]
    
    old_ids = state.get("drive", [])
    for f_id in new_ids:
        if f_id not in old_ids:
            f = next(file for file in files if file['id'] == f_id)
            log_event(f"DRIVE: Новый файл! {f['name']}", notify=True)
    
    state["drive"] = new_ids

def check_whatsapp(state):
    if not os.path.exists(WHATSAPP_FILE): return
    with open(WHATSAPP_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    last_line_idx = state.get("whatsapp_last_line", 0)
    if len(lines) > last_line_idx:
        new_lines = lines[last_line_idx:]
        for line in new_lines:
            if line.strip():
                log_event(f"WHATSAPP: {line.strip()}")
        state["whatsapp_last_line"] = len(lines)

def heartbeat():
    log_event("Сенсор событий запущен (heartbeat).")
    while True:
        state = get_state()
        try:
            check_gmail(state)
            check_tasks(state)
            check_drive(state)
            check_whatsapp(state)
            save_state(state)
        except Exception as e:
            log_event(f"ERROR: {e}")
        
        time.sleep(300) # Проверка каждые 5 минут

if __name__ == '__main__':
    heartbeat()
