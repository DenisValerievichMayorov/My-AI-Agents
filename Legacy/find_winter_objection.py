import imaplib
import email
from email.header import decode_header

EMAIL = 'denisvalerievichmayorov1@gmail.com'
PASSWORD = 'poehpeamrkxpzcfy'

try:
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(EMAIL, PASSWORD)
    
    # Check sent folder
    status, _ = mail.select('"[Gmail]/&BBoEPgRABDcEOAQ9BDA-"', readonly=True)
    if status != 'OK':
        status, _ = mail.select('"[Gmail]/Sent Mail"', readonly=True)

    # Search criteria
    status, messages = mail.search(None, '(OR TO "minfin" (OR BODY "rekening" BODY "belasting"))')
    if status == 'OK' and messages[0]:
        mail_ids = messages[0].split()
        for m_id in mail_ids[-15:]:
            status, data = mail.fetch(m_id, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])
            date_ = msg.get('Date')
            subj = decode_header(msg.get('Subject', ''))[0]
            subject = subj[0]
            if isinstance(subject, bytes):
                subject = subject.decode(subj[1] or 'utf-8', errors='ignore')
            
            body = ''
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                
            print(f"--- Date: {date_} | Subj: {subject}")
            print(body[:300].strip())
            print("="*40)
except Exception as e:
    print("Error:", e)
