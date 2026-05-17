import imaplib
import email
from email.header import decode_header
import os

EMAIL = "denisvalerievichmayorov1@gmail.com"
PASSWORD = "poehpeamrkxpzcfy"
IMAP_SERVER = "imap.gmail.com"
SAVE_DIR = "Werkraports/LawyerDocs"

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

def main():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)

    drafts = "[Gmail]/&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-"
    inbox = "INBOX"

    # Keywords suggesting lawyer/court correspondence
    lawyer_keywords = [
        'SUBJECT "advocaat"',
        'SUBJECT "rechtbank"',
        'SUBJECT "juridisch"',
        'SUBJECT "jurist"',
        'SUBJECT "deurwaarder"',
        'SUBJECT "syntheseconclusie"',
        'SUBJECT "conclusie"',
        'SUBJECT "zitting"',
        'SUBJECT "MAIOROV"',
        'SUBJECT "dossier"',
        'TO "advocaat"',
        'TO "rechtbank"',
        'SUBJECT "Re: FW"',
        'SUBJECT "opmerkingen"',
    ]

    os.makedirs(SAVE_DIR, exist_ok=True)

    for folder in [drafts, inbox]:
        print(f"\n### Searching folder: {folder} ###")
        try:
            status, _ = mail.select(f'"{folder}"', readonly=True)
            if status != 'OK':
                print(f"  Could not select {folder}")
                continue

            found_ids = set()
            for kw in lawyer_keywords:
                try:
                    status, messages = mail.search(None, kw)
                    if status == 'OK' and messages[0]:
                        for m_id in messages[0].split():
                            found_ids.add(m_id)
                except:
                    pass

            print(f"  Found {len(found_ids)} emails with lawyer/court keywords")

            for m_id in sorted(found_ids):
                status, data = mail.fetch(m_id, '(RFC822)')
                if status != 'OK':
                    continue
                msg = email.message_from_bytes(data[0][1])
                subj = get_subject(msg)
                from_ = msg.get("From","")
                to_ = msg.get("To","")
                date_ = msg.get("Date","")

                attachments = []
                if msg.is_multipart():
                    for part in msg.walk():
                        content_disposition = str(part.get("Content-Disposition",""))
                        if "attachment" in content_disposition:
                            filename = part.get_filename()
                            if filename:
                                fname_parts = decode_header(filename)
                                fname = ""
                                for fp, fenc in fname_parts:
                                    if isinstance(fp, bytes):
                                        fname += fp.decode(fenc or 'utf-8', errors='replace')
                                    else:
                                        fname += fp
                                attachments.append((fname, part.get_payload(decode=True)))

                print(f"\n  [{date_}]")
                print(f"  FROM: {from_}")
                print(f"  TO  : {to_}")
                print(f"  SUBJ: {subj}")

                if attachments:
                    print(f"  ATTACHMENTS ({len(attachments)}):")
                    for fname, content in attachments:
                        ext = os.path.splitext(fname)[1].lower()
                        print(f"    - {fname} ({len(content) if content else 0} bytes)")
                        if ext in ['.pdf', '.jpg', '.jpeg', '.png', '.docx', '.doc']:
                            save_path = os.path.join(SAVE_DIR, fname)
                            # avoid overwriting with same name
                            if os.path.exists(save_path):
                                base, ext2 = os.path.splitext(fname)
                                save_path = os.path.join(SAVE_DIR, f"{base}_{m_id.decode()}{ext2}")
                            if content:
                                with open(save_path, 'wb') as f:
                                    f.write(content)
                                print(f"      -> Saved: {save_path}")
                else:
                    print("  No attachments")

        except Exception as e:
            print(f"  ERROR: {e}")

    mail.logout()
    print(f"\nAll documents saved to: {SAVE_DIR}")

if __name__ == "__main__":
    main()
