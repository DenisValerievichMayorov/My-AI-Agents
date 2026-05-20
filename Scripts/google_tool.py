import os
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SYNC_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(SYNC_DIR, 'google_token.json')

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata',
    'https://www.googleapis.com/auth/tasks'
]

def get_creds(required_scopes):
    """
    Интеллектуальное получение учетных данных с изоляцией областей видимости.
    Если токен не содержит расширенных прав (например, на запись), возвращает
    только разрешенные области видимости или None для корректного переключения на локальный резерв.
    """
    if os.path.exists(TOKEN_PATH):
        try:
            # Пробуем загрузить токен с запрашиваемыми областями видимости
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, required_scopes)
            # Быстрая проверка валидности
            if creds and creds.valid:
                return creds
            # Если токен истек, пробуем обновить
            if creds and creds.expired and creds.refresh_token:
                from google.auth.transport.requests import Request
                creds.refresh(Request())
                return creds
        except Exception:
            # В случае несовпадения scopes или сбоя, не падаем, а позволяем вызвать fallback
            return None
    return None

def list_calendar():
    creds = get_creds(['https://www.googleapis.com/auth/calendar.readonly'])
    if not creds: return "Ошибка: Нет доступа к Календарю Google (требуется авторизация)."
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=5, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])
        if not events: return "Ближайших событий не найдено."
        
        res = "Ваши ближайшие события:\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            res += f"- {start}: {event.get('summary')}\n"
        return res
    except Exception as e: return f"Ошибка Календаря: {e}"

def search_gmail(query):
    creds = get_creds(['https://www.googleapis.com/auth/gmail.readonly'])
    if not creds: return "Ошибка: Нет доступа к Gmail (требуется авторизация)."
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', q=query, maxResults=3).execute()
        messages = results.get('messages', [])
        if not messages: return f"По запросу '{query}' ничего не найдено."
        
        res = f"Результаты поиска в Gmail по '{query}':\n"
        for m in messages:
            msg = service.users().messages().get(userId='me', id=m['id']).execute()
            headers = msg.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            from_ = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date_ = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            snippet = msg.get('snippet')
            res += f"- [{date_}] From: {from_}\n  Subject: {subject}\n  Snippet: {snippet}\n"
        return res
    except Exception as e: return f"Ошибка Gmail: {e}"

def create_gmail_draft(subject, to, body):
    # Запрашиваем compose scope
    creds = get_creds(['https://www.googleapis.com/auth/gmail.compose'])
    if not creds:
        # Автоматический запуск локального резервного сценария
        return save_local_draft(subject, to, body, "Нет прав gmail.compose в текущем токене")
        
    try:
        import base64
        from email.message import EmailMessage
        service = build('gmail', 'v1', credentials=creds)
        
        message = EmailMessage()
        message.set_content(body)
        message['To'] = to
        message['Subject'] = subject
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {
            'message': {
                'raw': encoded_message
            }
        }
        draft = service.users().drafts().create(userId="me", body=create_message).execute()
        return f"✅ Черновик письма успешно создан в Gmail! ID черновика: {draft.get('id')}"
    except Exception as e:
        return save_local_draft(subject, to, body, str(e))

def save_local_draft(subject, to, body, reason):
    draft_file = os.path.join(SYNC_DIR, "prepared_drafts.txt")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(draft_file, 'a', encoding='utf-8') as f:
        f.write(f"\n--- Черновик от {timestamp} ---\nКому: {to}\nТема: {subject}\n\n{body}\n----------------------\n")
    return f"⚠️ Резервный режим ({reason}): Черновик успешно подготовлен локально в prepared_drafts.txt и синхронизирован через Syncthing!"

def list_tasks():
    creds = get_creds(['https://www.googleapis.com/auth/tasks'])
    if not creds: return "Ошибка: Нет доступа к Google Tasks (требуется авторизация)."
    try:
        service = build('tasks', 'v1', credentials=creds)
        results = service.tasklists().list(maxResults=10).execute()
        items = results.get('items', [])
        if not items: return "Списков задач не найдено."
        
        res = "📋 Ваши списки задач Google Tasks:\n"
        for item in items:
            res += f"- {item.get('title')} (ID: {item.get('id')})\n"
        res += "\n📌 Активные задачи в основном списке:\n"
        
        tasks_result = service.tasks().list(tasklist='@default', maxResults=20, showCompleted=False).execute()
        tasks = tasks_result.get('items', [])
        if not tasks:
            res += "  (Нет активных задач)\n"
        else:
            for task in tasks:
                notes = f" — {task.get('notes')}" if task.get('notes') else ""
                res += f"  [ ] {task.get('title')}{notes}\n"
        return res
    except Exception as e:
        return f"Ошибка Tasks: {e}"

def add_task(title, notes=None, tasklist_id='@default'):
    creds = get_creds(['https://www.googleapis.com/auth/tasks'])
    if not creds:
        return save_local_task(title, notes, "Нет прав tasks в текущем токенах")
        
    try:
        service = build('tasks', 'v1', credentials=creds)
        task_body = {
            'title': title,
            'notes': notes
        }
        result = service.tasks().insert(tasklist=tasklist_id, body=task_body).execute()
        return f"✅ Задача '{title}' успешно добавлена в Google Tasks! ID: {result.get('id')}"
    except Exception as e:
        return save_local_task(title, notes, str(e))

def save_local_task(title, notes, reason):
    tasks_file = os.path.join(SYNC_DIR, "prepared_tasks.txt")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(tasks_file, 'a', encoding='utf-8') as f:
        f.write(f"- [ ] {title} ({notes or ''}) [Подготовлено: {timestamp}]\n")
    return f"⚠️ Резервный режим ({reason}): Задача записана в prepared_tasks.txt и синхронизирована через Syncthing!"

def list_photos():
    creds = get_creds(['https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata'])
    if not creds: return "Ошибка: Нет доступа к Google Photos."
    try:
        service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)
        results = service.mediaItems().list(pageSize=5).execute()
        items = results.get('mediaItems', [])
        if not items: return "Фото не найдено."
        
        res = "Последние фото в Google Photos:\n"
        for item in items:
            res += f"- {item.get('filename')} ({item.get('mimeType')})\n"
        return res
    except Exception as e: return f"Ошибка Фото: {e}"

def list_drive():
    creds = get_creds(['https://www.googleapis.com/auth/drive.readonly'])
    if not creds: return "Ошибка: Нет доступа к Google Drive."
    try:
        service = build('drive', 'v3', credentials=creds)
        results = service.files().list(
            pageSize=5, fields="nextPageToken, files(id, name, mimeType)").execute()
        items = results.get('files', [])
        if not items: return "Файлы в Drive не найдены."
        
        res = "Последние файлы в Google Drive:\n"
        for item in items:
            res += f"- {item.get('name')} ({item.get('mimeType')})\n"
        return res
    except Exception as e: return f"Ошибка Drive: {e}"

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'gmail' and len(sys.argv) > 2:
            print(search_gmail(sys.argv[2]))
        elif cmd == 'draft' and len(sys.argv) > 4:
            print(create_gmail_draft(sys.argv[2], sys.argv[3], sys.argv[4]))
        elif cmd == 'task' and len(sys.argv) > 2:
            notes = sys.argv[3] if len(sys.argv) > 3 else None
            print(add_task(sys.argv[2], notes))
        elif cmd == 'tasks':
            print(list_tasks())
        elif cmd == 'calendar':
            print(list_calendar())
        elif cmd == 'drive':
            print(list_drive())
        elif cmd == 'photos':
            print(list_photos())
    else:
        print(list_calendar())
        print("-" * 30)
        print(list_drive())
        print("-" * 30)
        print(list_photos())
