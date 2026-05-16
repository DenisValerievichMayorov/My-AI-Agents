import os
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SYNC_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(SYNC_DIR, 'google_token.json')
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/photoslibrary.readonly'
]

def get_creds():
    if os.path.exists(TOKEN_PATH):
        return Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    return None

def list_calendar():
    creds = get_creds()
    if not creds: return "Ошибка: Нет доступа к Google (запустите google_auth.py)"
    
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
    creds = get_creds()
    if not creds: return "Ошибка: Нет доступа."
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', q=query, maxResults=3).execute()
        messages = results.get('messages', [])
        if not messages: return f"По запросу '{query}' ничего не найдено."
        
        res = f"Результаты поиска в Gmail по '{query}':\n"
        for m in messages:
            msg = service.users().messages().get(userId='me', id=m['id']).execute()
            snippet = msg.get('snippet')
            res += f"- {snippet}\n"
        return res
    except Exception as e: return f"Ошибка Gmail: {e}"

def list_photos():
    creds = get_creds()
    if not creds: return "Ошибка: Нет доступа."
    # API для Фото немного специфичное
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
    creds = get_creds()
    if not creds: return "Ошибка: Нет доступа."
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
    print(list_calendar())
    print("-" * 30)
    print(list_drive())
    print("-" * 30)
    print(list_photos())
