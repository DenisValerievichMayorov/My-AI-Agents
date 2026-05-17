import imaplib
import email
from email.header import decode_header

EMAIL = "denisvalerievichmayorov1@gmail.com"
PASSWORD = "poehpeamrkxpzcfy"
IMAP_SERVER = "imap.gmail.com"

def get_header(msg, name):
    raw = msg.get(name, "")
    parts = decode_header(raw)
    result = ""
    for part, enc in parts:
        if isinstance(part, bytes):
            result += part.decode(enc or 'utf-8', errors='replace')
        else:
            result += part
    return result

def main():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    
    # "Отправленные" represented by [Gmail]/&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-
    sent_folder = "[Gmail]/&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-"
    print(f"Selecting folder: {sent_folder}")
    status, _ = mail.select(f'"{sent_folder}"', readonly=True)
    if status != 'OK':
        print("Failed to select folder")
        return
        
    status, messages = mail.search(None, 'ALL')
    if status != 'OK' or not messages[0]:
        print("No messages found")
        return
        
    ids = messages[0].split()
    print(f"Total sent emails: {len(ids)}")
    
    # Let's inspect the last 50 sent emails
    for m_id in reversed(ids[-50:]):
        try:
            status, data = mail.fetch(m_id, '(BODY[HEADER.FIELDS (SUBJECT TO DATE)])')
            if status != 'OK':
                continue
            msg = email.message_from_bytes(data[0][1])
            to = get_header(msg, 'To')
            subj = get_header(msg, 'Subject')
            date = get_header(msg, 'Date')
            print(f"[{date}] TO: {to} | SUBJ: {subj}")
        except Exception as e:
            print(f"Error fetching {m_id}: {e}")
            
    mail.logout()

if __name__ == "__main__":
    main()
