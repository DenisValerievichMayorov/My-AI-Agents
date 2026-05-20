import os
import sys

# Add scripts directory to path to import google_tool
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

import google_tool
from googleapiclient.discovery import build

def fetch_recent_emails(limit=10):
    creds = google_tool.get_creds()
    if not creds:
        print("Error: No Google credentials found.")
        return

    try:
        service = build('gmail', 'v1', credentials=creds)
        # Fetch the most recent 10 messages from the inbox
        results = service.users().messages().list(userId='me', q="label:INBOX", maxResults=limit).execute()
        messages = results.get('messages', [])
        if not messages:
            print("No recent messages found in inbox.")
            return

        print(f"--- Fetching {len(messages)} most recent emails ---")
        for m in messages:
            msg = service.users().messages().get(userId='me', id=m['id']).execute()
            headers = msg.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            from_ = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date_ = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            snippet = msg.get('snippet', '')
            
            print(f"\nID: {m['id']}")
            print(f"Date: {date_}")
            print(f"From: {from_}")
            print(f"Subject: {subject}")
            print(f"Snippet: {snippet}")
            print("-" * 50)
            
    except Exception as e:
        print(f"Error fetching emails: {e}")

if __name__ == '__main__':
    fetch_recent_emails()
