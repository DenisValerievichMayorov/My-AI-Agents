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
    'https://www.googleapis.com/auth/photoslibrary.readonly',
    'https://www.googleapis.com/auth/photoslibrary'
]

def get_creds():
    if os.path.exists(TOKEN_PATH):
        return Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    return None

def test_photos_albums():
    creds = get_creds()
    if not creds: return "Нет токена"
    try:
        service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)
        results = service.albums().list(pageSize=5).execute()
        albums = results.get('albums', [])
        print(f"Найдено альбомов: {len(albums)}")
        for a in albums:
            print(f"- {a.get('title')}")
    except Exception as e:
        print(f"Ошибка альбомов: {e}")

if __name__ == '__main__':
    test_photos_albums()
