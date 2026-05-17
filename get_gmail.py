import imaplib
import email
from email.header import decode_header
import datetime

EMAIL = "denisvalerievichmayorov1@gmail.com"
PASSWORD = "poehpeamrkxpzcfy"
IMAP_SERVER = "imap.gmail.com"

def search_abvv():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        # Более широкий поиск именно по ABVV/FGTB (только непрочитанные)
        search_query = '(UNSEEN (OR FROM "ABVV" (OR FROM "FGTB" (OR SUBJECT "ABVV" SUBJECT "FGTB"))))'
        
        # Поиск за 60 дней
        date = (datetime.date.today() - datetime.timedelta(days=60)).strftime("%d-%b-%Y")
        
        print(f"Поиск писем от ABVV/FGTB с {date}...\n")
        status, messages = mail.search(None, f'{search_query} (SINCE "{date}")')
        
        if status == 'OK' and messages[0]:
            mail_ids = messages[0].split()
            print(f"Найдено писем: {len(mail_ids)}\n")
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
                print("-" * 50)
        else:
            print("Писем от ABVV (FGTB) не найдено.")

        mail.logout()
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    search_abvv()
