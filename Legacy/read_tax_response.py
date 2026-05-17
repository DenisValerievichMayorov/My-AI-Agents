import imaplib
import email
from email.header import decode_header
import re

EMAIL = "denisvalerievichmayorov1@gmail.com"
PASSWORD = "poehpeamrkxpzcfy"
IMAP_SERVER = "imap.gmail.com"

def get_body(msg):
    text_content = ""
    html_content = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            decoded = payload.decode('utf-8', errors='replace')
            if ct == "text/plain":
                text_content += decoded
            elif ct == "text/html":
                html_content += decoded
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            text_content = payload.decode('utf-8', errors='replace')
    if text_content.strip():
        return text_content.strip()
    # fallback: strip HTML
    clean = re.sub(r'<[^>]+>', ' ', html_content)
    clean = re.sub(r'[ \t]+', ' ', clean)
    clean = re.sub(r'\n{3,}', '\n\n', clean)
    return clean.strip()

def get_subject(msg):
    raw = msg.get("Subject", "")
    parts = decode_header(raw)
    result = ""
    for part, enc in parts:
        if isinstance(part, bytes):
            result += part.decode(enc or 'utf-8', errors='replace')
        else:
            result += part
    return result

def search_and_print(mail, folder, criteria):
    try:
        status, _ = mail.select(f'"{folder}"', readonly=True)
        if status != 'OK':
            return
        status, messages = mail.search(None, criteria)
        if status != 'OK' or not messages[0]:
            return
        ids = messages[0].split()
        print(f"  -> {len(ids)} hit(s) in '{folder}' for: {criteria}")
        for m_id in ids:
            status, data = mail.fetch(m_id, '(RFC822)')
            if status != 'OK':
                continue
            msg = email.message_from_bytes(data[0][1])
            subj = get_subject(msg)
            from_ = msg.get("From","")
            to_ = msg.get("To","")
            date_ = msg.get("Date","")
            body = get_body(msg)
            print(f"\n{'='*65}")
            print(f"DATE   : {date_}")
            print(f"FROM   : {from_}")
            print(f"TO     : {to_}")
            print(f"SUBJECT: {subj}")
            print(f"{'='*65}")
            print(body[:3000])
    except Exception as e:
        print(f"  ERROR: {e}")

def main():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)

    inbox = "INBOX"
    drafts = "[Gmail]/&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-"

    print("\n### INBOX: replies FROM minfin.fed.be ###")
    search_and_print(mail, inbox, 'FROM "minfin.fed.be"')

    print("\n### INBOX: SUBJECT bezwaar ###")
    search_and_print(mail, inbox, 'SUBJECT "bezwaar"')

    print("\n### INBOX: SUBJECT aanslag ###")
    search_and_print(mail, inbox, 'SUBJECT "aanslag"')

    print("\n### INBOX: SUBJECT invordering ###")
    search_and_print(mail, inbox, 'SUBJECT "invordering"')

    print("\n### INBOX: SUBJECT terugbetaling belasting ###")
    search_and_print(mail, inbox, 'SUBJECT "terugbetaling"')

    print("\n### DRAFTS: bezwaar / aanslag / invordering / 965 ###")
    for kw in ["bezwaar", "aanslag", "invordering", "965", "terugbetaling"]:
        search_and_print(mail, drafts, f'SUBJECT "{kw}"')

    mail.logout()

if __name__ == "__main__":
    main()
