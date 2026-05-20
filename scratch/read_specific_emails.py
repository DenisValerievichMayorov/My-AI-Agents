import os
import sys

scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

import google_tool
from googleapiclient.discovery import build
import base64

def get_email_body(service, msg_id):
    msg_detail = service.users().messages().get(userId='me', id=msg_id).execute()
    payload = msg_detail.get('payload', {})
    snippet = msg_detail.get('snippet', '')
    
    body_text = ""
    def parse_parts(parts):
        nonlocal body_text
        for part in parts:
            mimeType = part.get('mimeType', '')
            filename = part.get('filename', '')
            body = part.get('body', {})
            data = body.get('data')

            if 'parts' in part:
                parse_parts(part['parts'])

            if mimeType == 'text/plain' and data and not filename:
                try:
                    text = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                    body_text += text + '\n'
                except:
                    pass
            elif mimeType == 'text/html' and data and not filename and not body_text:
                try:
                    text = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                    body_text += text + '\n'
                except:
                    pass

    if 'parts' in payload:
        parse_parts(payload['parts'])
    elif payload.get('body', {}).get('data'):
        try:
            body_text += base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
        except:
            pass
            
    if not body_text:
        body_text = snippet
        
    return body_text

def read_emails():
    creds = google_tool.get_creds()
    if not creds:
        print("No creds found.")
        return
        
    service = build('gmail', 'v1', credentials=creds)
    ids = ['19e356e3cf0c64cf', '19e35423881c877f']
    
    for mid in ids:
        print(f"\n================ Email ID: {mid} ================")
        body = get_email_body(service, mid)
        print(body[:3000]) # Limit to 3000 chars for readability
        print("==================================================")

if __name__ == '__main__':
    read_emails()
