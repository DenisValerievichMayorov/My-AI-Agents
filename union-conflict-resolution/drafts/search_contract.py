import imaplib
import email
from email.header import decode_header
import datetime
import os

EMAIL = "denisvalerievichmayorov1@gmail.com"
PASSWORD = "poehpeamrkxpzcfy"
IMAP_SERVER = "imap.gmail.com"

def search_contract():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        # Поиск писем от Sofie или со словом Contract
        search_query = '(OR FROM "Sofie" SUBJECT "Contract")'
        
        print(f"Поиск контракта от Sofie в почте {EMAIL}...\n")
        status, messages = mail.search(None, search_query)
        
        if status == 'OK' and messages[0]:
            mail_ids = messages[0].split()
            print(f"Найдено писем: {len(mail_ids)}\n")
            
            # Создаем папку для вложений, если её нет
            evidence_dir = "union-conflict-resolution/evidence"
            if not os.path.exists(evidence_dir):
                os.makedirs(evidence_dir)

            for m_id in mail_ids:
                status, data = mail.fetch(m_id, '(RFC822)')
                msg = email.message_from_bytes(data[0][1])
                
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8", errors="replace")
                
                from_ = msg.get("From")
                date_ = msg.get("Date")
                
                print(f"[{date_}] {from_}")
                print(f"Тема: {subject}")
                
                # Ищем вложения
                for part in msg.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue
                        
                    filename = part.get_filename()
                    if filename:
                        decoded_filename, encoding = decode_header(filename)[0]
                        if isinstance(decoded_filename, bytes):
                            decoded_filename = decoded_filename.decode(encoding if encoding else "utf-8", errors="replace")
                        
                        # Сохраняем файл в evidence
                        filepath = os.path.join(evidence_dir, decoded_filename)
                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        print(f"  -> Вложение сохранено: {filepath}")
                
                print("-" * 50)
        else:
            print("Писем от Sofie или с темой 'Contract' не найдено.")

        mail.logout()
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    search_contract()
