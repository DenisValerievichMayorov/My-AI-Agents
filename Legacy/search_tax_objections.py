import imaplib
import email
from email.header import decode_header
import datetime

EMAIL = "denisvalerievichmayorov1@gmail.com"
PASSWORD = "poehpeamrkxpzcfy"
IMAP_SERVER = "imap.gmail.com"

def search_tax():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        
        # Получаем список папок
        status, folders = mail.list()
        print("Доступные папки:")
        for folder in folders:
            print(folder.decode())
            
        sent_folder = None
        for folder in folders:
            folder_str = folder.decode()
            if '\\Sent' in folder_str:
                parts = folder_str.split(' "/" ')
                if len(parts) > 1:
                    sent_folder = parts[1] # Это имя в кавычках, например "[Gmail]/&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-"
                    break
        
        if sent_folder:
            print(f"Выбираем папку: {sent_folder}")
            status, _ = mail.select(sent_folder)
            if status != 'OK':
                print(f"Не удалось выбрать папку {sent_folder}, статус: {status}")
                return
        else:
            print("Папка с атрибутом \\Sent не найдена.")
            return

        print(f"Текущая папка: {sent_folder}")

        # Поиск по ключевым словам: возражения, налоговая, nalog
        # IMAP SEARCH не очень хорошо работает с кириллицей в некоторых реализациях, 
        # но Gmail поддерживает CHARSET UTF-8
        
        # Вместо поиска, который глючит с кириллицей, получим последние 100 писем
        # и проверим их темы и содержимое локально.
        status, messages = mail.search(None, 'ALL')
        if status == 'OK' and messages[0]:
            mail_ids = messages[0].split()
            print(f"Всего отправленных писем: {len(mail_ids)}")
            
            # Попробуем найти папку "Вся почта"
        all_mail_folder = None
        for folder in folders:
            folder_str = folder.decode()
            if '\\All' in folder_str:
                parts = folder_str.split(' "/" ')
                if len(parts) > 1:
                    all_mail_folder = parts[1]
                    break
        
        if not all_mail_folder:
            print("Папка 'Вся почта' не найдена.")
            return

        print(f"Выбираем папку: {all_mail_folder}")
        mail.select(all_mail_folder)

        # Поиск по профсоюзам
        queries = [
            "ACV", "VSOA", "ABVV", "ACLVB", "VCA", "vakbond", "syndicaat", 
            "lidmaatschap", "bijdrage", "premie"
        ]
        
        found = False
        for q in queries:
            print(f"Поиск: {q}")
            try:
                # В папке "Вся почта"
                status, messages = mail.search(None, 'X-GM-RAW', q.encode('utf-8'))
                if status == 'OK' and messages[0]:
                    mail_ids = messages[0].split()
                    print(f"Найдено ({q}): {len(mail_ids)}")
                    # Проверяем последние 20 писем для каждого запроса
                    for m_id in mail_ids[-20:]:
                        status, data = mail.fetch(m_id, '(BODY[HEADER.FIELDS (SUBJECT TO FROM DATE)])')
                        msg = email.message_from_bytes(data[0][1])
                        
                        subject, encoding = decode_header(msg.get("Subject", ""))[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8", errors="replace")
                        
                        from_ = msg.get("From", "")
                        to_ = msg.get("To", "")
                        date_ = msg.get("Date", "")
                        
                        # Выводим только если это похоже на профсоюз или подтверждение
                        print(f"[{date_}] От: {from_} Кому: {to_}")
                        print(f"Тема: {subject}")
                        print("-" * 50)
                        found = True
                else:
                    print(f"Ничего не найдено для {q}")
            except Exception as e:
                print(f"Ошибка поиска {q}: {e}")

        # Получаем полный текст письма от 16 апреля 2026 года
        print("\nПолучаем детали письма от 16 апреля 2026...")
        # Поиск конкретно этого письма по теме
        status, messages = mail.search(None, 'X-GM-RAW', 'subject:"Bezwaarschrift tegen aanslagbiljet AJ 2025"')
        if status == 'OK' and messages[0]:
            mail_id = messages[0].split()[-1] # Берем самое свежее (или единственное)
            status, data = mail.fetch(mail_id, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])
            
            print(f"Тема: {msg['Subject']}")
            print(f"Дата: {msg['Date']}")
            print(f"Кому: {msg['To']}")
            
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
            
            print("\nТекст письма:")
            print(body)
        else:
            print("Письмо не найдено при повторном поиске.")

        mail.logout()
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    search_tax()
