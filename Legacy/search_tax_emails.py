import imaplib
import email
from email.header import decode_header
import os

EMAIL = "denisvalerievichmayorov1@gmail.com"
PASSWORD = "poehpeamrkxpzcfy"
IMAP_SERVER = "imap.gmail.com"
SAVE_DIR = "Werkraports"

def search_tax_emails():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        
        print("Listing available folders:")
        status, folder_list = mail.list()
        folders = []
        if status == 'OK':
            for f in folder_list:
                f_name = f.decode('utf-8')
                if '"' in f_name:
                    folders.append(f_name.split('"')[-2])
                else:
                    folders.append(f_name.split()[-1])
                print(f" - {folders[-1]}")
        
        # Candidates to check
        candidates = ["INBOX"]
        for f in folders:
            f_lower = f.lower()
            if any(term in f_lower for term in ["all", "вся", "alle", "sent", "отправленные"]):
                if f not in candidates:
                    candidates.append(f)
        # Force add Russian UTF-7 localized folder names
        candidates = [
            "INBOX", 
            "[Gmail]/&BBoEPgRABDcEOAQ9BDA-", # Sent Mail (Отправленные)
            "[Gmail]/&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-", # Drafts (Черновики)
            "[Gmail]/&BCcENQRABD0EPgQyBDgEOgQ4-", # All Mail (Вся почта)
        ]
        print(f"\nSearching in folders: {candidates}")
        search_query = '(OR (OR SUBJECT "belasting" SUBJECT "tax") (OR SUBJECT "fiscus" SUBJECT "myminfin"))'
        
        found_emails = []
        for folder in candidates:
            try:
                print(f"Selecting '{folder}'...")
                status, select_data = mail.select(f'"{folder}"', readonly=True)
                if status != 'OK':
                    continue
                
                # First let's search with our standard tax subject search
                status, messages = mail.search(None, search_query)
                if status == 'OK' and messages[0]:
                    mail_ids = messages[0].split()
                    print(f"Found {len(mail_ids)} matches in '{folder}'.")
                    for m_id in mail_ids:
                        if (folder, m_id) not in found_emails:
                            found_emails.append((folder, m_id))
                
                # Also fallback to search for ANY recent email (last 20) in Sent or Drafts
                if folder != "INBOX":
                    status, messages = mail.search(None, "ALL")
                    if status == 'OK' and messages[0]:
                        mail_ids = messages[0].split()
                        # Add last 20 emails from Sent or Drafts to candidates to parse in python
                        for m_id in mail_ids[-20:]:
                            if (folder, m_id) not in found_emails:
                                found_emails.append((folder, m_id))
            except Exception as fe:
                print(f"Error reading folder '{folder}': {fe}")
                
        if found_emails:
            print(f"\nProcessing the most recent {min(5, len(found_emails))} tax emails:")
            # Sort to show most recent first
            for folder, m_id in reversed(found_emails[-5:]):
                mail.select(f'"{folder}"', readonly=True)
                status, data = mail.fetch(m_id, '(RFC822)')
                if status != 'OK':
                    continue
                
                msg = email.message_from_bytes(data[0][1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8", errors="replace")
                
                from_ = msg.get("From")
                date_ = msg.get("Date")
                
                text_content = ""
                attachments = []
                
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
                        
                print(f"\n=================== EMAIL FOUND ===================")
                print(f"Folder: {folder}")
                print(f"Date: {date_}")
                print(f"From: {from_}")
                print(f"Subject: {subject}")
                print(f"Attachments: {[f[0] for f in attachments]}")
                print(f"Body:\n{text_content.strip()[:1500]}\n")
                
                for filename, content in attachments:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.webp', '.pdf']:
                        if not os.path.exists(SAVE_DIR):
                            os.makedirs(SAVE_DIR)
                        save_path = os.path.join(SAVE_DIR, filename)
                        with open(save_path, 'wb') as f:
                            f.write(content)
                        print(f"Saved attachment to: {save_path}")
                print("=" * 51)
        else:
            print("\nNo tax-related emails found in any of the folders.")
            
        mail.logout()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_tax_emails()
