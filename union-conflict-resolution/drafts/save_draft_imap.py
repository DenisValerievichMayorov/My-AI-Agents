import imaplib
import time
from email.message import EmailMessage

EMAIL = "denisvalerievichmayorov1@gmail.com"
PASSWORD = "poehpeamrkxpzcfy"
IMAP_SERVER = "imap.gmail.com"

def save_draft():
    # Читаем черновик
    with open("union-conflict-resolution/drafts/2026-05-14_union_letter_ru.md", "r", encoding="utf-8") as f:
        body = f.read()

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = "Конфликт с работодателем: PC 149.01, личный транспорт и неоплата времени"
    msg["From"] = EMAIL
    msg["To"] = "info@abvv.be" # Заглушка, профсоюз

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        
        # Gmail требует специальное имя папки для черновиков
        # Обычно это "[Gmail]/Drafts" или "[Gmail]/Черновики"
        # Мы попробуем найти её
        status, folders = mail.list()
        draft_folder = "[Gmail]/Drafts"
        for folder in folders:
            folder_str = folder.decode()
            if "Drafts" in folder_str or "Черновики" in folder_str:
                draft_folder = folder_str.split(' "/" ')[-1].strip('"')
                break

        print(f"Сохранение в папку: {draft_folder}")
        
        # Append expects bytes and time
        mail.append(draft_folder, '', imaplib.Time2Internaldate(time.time()), msg.as_bytes())
        
        print("Черновик успешно сохранен!")
        mail.logout()
    except Exception as e:
        print(f"Ошибка при сохранении черновика: {e}")

if __name__ == "__main__":
    save_draft()
