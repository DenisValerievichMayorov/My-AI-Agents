import imaplib
import time
from email.message import EmailMessage

EMAIL = "denisvalerievichmayorov1@gmail.com"
PASSWORD = "poehpeamrkxpzcfy"
IMAP_SERVER = "imap.gmail.com"

def save_draft(subject, file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        body = f.read()

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = "info@abvv.be"

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
    # Сохраняем нидерландскую версию
    if save_draft("Vakbond: Verzoek om toelichting (PC 149.01) - NL", "union-conflict-resolution/drafts/2026-05-14_union_letter_nl.md"):
        print("Версия на нидерландском сохранена.")
    
    # Сохраняем русскую версию
    if save_draft("Профсоюз: Запрос разъяснений (PC 149.01) - RU", "union-conflict-resolution/drafts/2026-05-14_union_letter_ru.md"):
        print("Версия на русском сохранена.")
