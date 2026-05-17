import imaplib
import email
from email.header import decode_header

EMAIL = "denisvalerievichmayorov1@gmail.com"
PASSWORD = "poehpeamrkxpzcfy"
IMAP_SERVER = "imap.gmail.com"

def get_body(msg):
    text_content = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    text_content += payload.decode('utf-8', errors='replace')
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            text_content = payload.decode('utf-8', errors='replace')
    return text_content.strip()

def read_drafts():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        
        # Select Drafts (Черновики)
        mail.select('"[Gmail]/&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-"')
        
        for d_id in ['564', '571']:
            print(f"\n==========================================")
            print(f"FETCHING DRAFT ID: {d_id}")
            print(f"==========================================")
            status, data = mail.fetch(d_id, '(RFC822)')
            if status == 'OK':
                msg = email.message_from_bytes(data[0][1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8", errors="replace")
                
                print(f"Subject: {subject}")
                print(f"Date: {msg.get('Date')}")
                print(f"From: {msg.get('From')}")
                print(f"To: {msg.get('To')}")
                print(f"\nBody:\n{get_body(msg)}")
                print("-" * 50)
            else:
                print(f"Failed to fetch draft {d_id}")
                
        mail.logout()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    read_drafts()
