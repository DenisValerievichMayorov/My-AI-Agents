import imaplib
import time
from email.message import EmailMessage

EMAIL = "denisvalerievichmayorov1@gmail.com"
PASSWORD = "poehpeamrkxpzcfy"
IMAP_SERVER = "imap.gmail.com"

def save_draft_with_attachments(subject, text_file, attachments):
    with open(text_file, "r", encoding="utf-8") as f:
        body = f.read()

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = "info@abvv.be"

    for file_path in attachments:
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
                file_name = file_path.split("/")[-1]
                msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=file_name)
        except Exception as e:
            print(f"Не удалось прикрепить {file_path}: {e}")

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        
        status, folders = mail.list()
        draft_folder = "[Gmail]/Drafts"
        for folder in folders:
            folder_str = folder.decode()
            if "Drafts" in folder_str or "Черновики" in folder_str:
                draft_folder = folder_str.split(' "/" ')[-1].strip('"')
                break

        mail.append(draft_folder, '', imaplib.Time2Internaldate(time.time()), msg.as_bytes())
        mail.logout()
        return True
    except Exception as e:
        print(f"Ошибка при сохранении {subject}: {e}")
        return False

if __name__ == "__main__":
    files_to_attach = [
        "union-conflict-resolution/evidence/arbeidsovereenkomst ondertekend.pdf",
        "union-conflict-resolution/evidence/Loonbrief april 2026.pdf"
    ]
    
    if save_draft_with_attachments("Vakbond: Verzoek om toelichting (PC 149.01) - NL (WITH ATTACHMENTS)", 
                                   "union-conflict-resolution/drafts/2026-05-14_union_letter_nl.md", 
                                   files_to_attach):
        print("Черновик с вложениями успешно сохранен.")
