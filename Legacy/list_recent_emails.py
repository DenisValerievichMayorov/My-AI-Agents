import imaplib
import email
from email.header import decode_header
import os

EMAIL = "denisvalerievichmayorov1@gmail.com"
PASSWORD = "poehpeamrkxpzcfy"
IMAP_SERVER = "imap.gmail.com"
SAVE_DIR = "Werkraports"

def list_recent_emails():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        
        # We will check INBOX, Sent, and Drafts
        folders = [
            "INBOX",
            "[Gmail]/&BBoEPgRABDcEOAQ9BDA-", # Sent Mail (Отправленные)
            "[Gmail]/&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-", # Drafts (Черновики)
        ]
        
        for folder in folders:
            print(f"\n==========================================")
            print(f"Checking folder: {folder}")
            print(f"==========================================")
            try:
                status, select_data = mail.select(f'"{folder}"', readonly=True)
                if status != 'OK':
                    print(f"Failed to select folder {folder}")
                    continue
                
                # Fetch all emails in this folder
                status, messages = mail.search(None, "ALL")
                if status == 'OK' and messages[0]:
                    mail_ids = messages[0].split()
                    print(f"Total emails in {folder}: {len(mail_ids)}")
                    
                    # Fetch the most recent 15 emails
                    for m_id in reversed(mail_ids[-15:]):
                        status, data = mail.fetch(m_id, '(RFC822)')
                        if status != 'OK':
                            continue
                        
                        msg = email.message_from_bytes(data[0][1])
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8", errors="replace")
                        
                        from_ = msg.get("From")
                        date_ = msg.get("Date")
                        
                        attachments = []
                        text_content = ""
                        
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                
                                if "attachment" in content_disposition:
                                    filename = part.get_filename()
                                    if filename:
                                        filename_dec, enc = decode_header(filename)[0]
                                        if isinstance(filename_dec, bytes):
                                            filename = filename_dec.decode(enc if enc else "utf-8", errors="replace")
                                        attachments.append((filename, part.get_payload(decode=True)))
                                elif content_type == "text/plain":
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        text_content += payload.decode('utf-8', errors='replace')
                        else:
                            payload = msg.get_payload(decode=True)
                            if payload:
                                text_content = payload.decode('utf-8', errors='replace')
                                
                        # Print summary
                        print(f"ID: {m_id.decode()} | Date: {date_} | Subject: {subject} | From: {from_}")
                        if attachments:
                            print(f"  -> ATTACHMENTS: {[f[0] for f in attachments]}")
                            # Save attachments
                            for filename, content in attachments:
                                ext = os.path.splitext(filename)[1].lower()
                                if ext in ['.jpg', '.jpeg', '.png', '.webp', '.pdf']:
                                    if not os.path.exists(SAVE_DIR):
                                        os.makedirs(SAVE_DIR)
                                    save_path = os.path.join(SAVE_DIR, filename)
                                    with open(save_path, 'wb') as f:
                                        f.write(content)
                                    print(f"  -> Saved attachment to: {save_path}")
                        if "налог" in subject.lower() or "belasting" in subject.lower() or "fiscus" in subject.lower() or "tax" in subject.lower():
                            print(f"  -> Body Snippet:\n{text_content.strip()[:600]}\n")
                            print("-" * 50)
                else:
                    print(f"No emails in {folder}")
            except Exception as e:
                print(f"Error checking folder {folder}: {e}")
                
        mail.logout()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_recent_emails()
