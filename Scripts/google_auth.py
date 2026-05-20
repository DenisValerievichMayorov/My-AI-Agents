import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Если вы измените эти области доступа, удалите файл token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata',
    'https://www.googleapis.com/auth/tasks'
]

def main():
    """Настройка доступа к Google API."""
    creds = None
    sync_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(sync_dir, 'google_token.json')
    creds_path = os.path.join(sync_dir, 'credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # Если нет валидных учетных данных, просим войти
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                print(f"❌ ОШИБКА: Файл {creds_path} не найден!")
                print("1. Зайдите в Google Cloud Console.")
                print("2. Создайте OAuth 2.0 Client ID (Desktop app).")
                print("3. Скачайте JSON и переименуйте его в 'credentials.json'.")
                print(f"4. Положите его в папку {sync_dir}.")
                return

            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Сохраняем токен для следующего раза
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print(f"✅ Успех! Токен сохранен в {token_path}")

if __name__ == '__main__':
    main()
