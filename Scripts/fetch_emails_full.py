import os
import datetime
import json
import base64
import argparse
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Конфигурация путей
SYNC_DIR = "/data/data/com.termux/files/home/Sync"
TOKEN_PATH = os.path.join(SYNC_DIR, "Scripts", "google_token.json")
EMAILS_DIR = os.path.join(SYNC_DIR, "Data", "emails")
ATTACHMENTS_DIR = os.path.join(SYNC_DIR, "Data", "email_attachments")
LOG_FILE = os.path.join(SYNC_DIR, "Logs", "email_fetch.log")

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(message)

def get_creds():
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return creds
    return None

def save_attachment(service, msg_id, part, filename):
    if 'data' in part['body']:
        data = part['body']['data']
    else:
        att_id = part['body']['attachmentId']
        att = service.users().messages().attachments().get(userId='me', messageId=msg_id, id=att_id).execute()
        data = att['data']
    
    file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
    path = os.path.join(ATTACHMENTS_DIR, f"{msg_id}_{filename}")
    with open(path, 'wb') as f:
        f.write(file_data)
    return path

def process_message(service, msg_info):
    msg_id = msg_info['id']
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    
    headers = msg.get('payload', {}).get('headers', [])
    metadata = {
        'id': msg_id,
        'threadId': msg['threadId'],
        'snippet': msg.get('snippet', ''),
        'subject': next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject'),
        'from': next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown'),
        'date': next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown'),
    }
    
    attachments = []
    body_text = ""
    
    def parse_parts(parts):
        nonlocal body_text
        for part in parts:
            mime_type = part.get('mimeType')
            filename = part.get('filename')
            if filename:
                att_path = save_attachment(service, msg_id, part, filename)
                attachments.append({'filename': filename, 'path': att_path})
            
            if mime_type == 'text/plain' and 'data' in part['body']:
                body_text += base64.urlsafe_b64decode(part['body']['data'].encode('UTF-8')).decode('utf-8', errors='ignore')
            elif mime_type == 'multipart/alternative' or mime_type.startswith('multipart/'):
                parse_parts(part.get('parts', []))

    payload = msg.get('payload', {})
    if 'parts' in payload:
        parse_parts(payload['parts'])
    elif 'body' in payload and 'data' in payload['body']:
        body_text = base64.urlsafe_b64decode(payload['body']['data'].encode('UTF-8')).decode('utf-8', errors='ignore')

    metadata['body'] = body_text
    metadata['attachments'] = attachments
    
    with open(os.path.join(EMAILS_DIR, f"{msg_id}.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return metadata['subject']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", type=int, default=6)
    args = parser.parse_args()
    
    creds = get_creds()
    if not creds:
        log("Error: No valid credentials found.")
        return

    service = build('gmail', 'v1', credentials=creds)
    
    # Расчет даты
    after_date = (datetime.datetime.now() - datetime.timedelta(days=args.months*30)).strftime("%Y/%m/%d")
    query = f"after:{after_date}"
    log(f"Searching for emails: {query}")
    
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = []
    
    while results.get('messages'):
        messages.extend(results.get('messages'))
        page_token = results.get('nextPageToken')
        if not page_token or len(messages) >= 2000: # Лимит для безопасности, чтобы не зависнуть на слишком долго
            break
        results = service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
    
    if not messages:
        log("No messages found.")
        return

    log(f"Found {len(messages)} messages. Starting download...")
    
    count = 0
    for m in messages:
        try:
            subject = process_message(service, m)
            count += 1
            if count % 10 == 0:
                log(f"Processed {count}/{len(messages)} messages...")
        except Exception as e:
            log(f"Error processing message {m['id']}: {e}")
            
    log(f"Finished! Total processed: {count}")

if __name__ == "__main__":
    main()
