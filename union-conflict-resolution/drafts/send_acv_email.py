import smtplib
from email.message import EmailMessage

# Данные отправителя
EMAIL = "denisvalerievichmayorov1@gmail.com"
PASSWORD = "poehpeamrkxpzcfy"  # Пароль приложения из конфига

# Данные получателя (общий адрес ACV)
RECIPIENT = "info@acv-csc.be"
SUBJECT = "Opzegging lidmaatschap en verzoek tot terugbetaling - Denys Maiorov"

def send_email():
    with open("union-conflict-resolution/drafts/ACV_opzegging_NL.md", "r", encoding="utf-8") as f:
        content = f.read()

    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = SUBJECT
    msg["From"] = EMAIL
    msg["To"] = RECIPIENT

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL, PASSWORD)
            smtp.send_message(msg)
        print("Письмо успешно отправлено в ACV.")
    except Exception as e:
        print(f"Ошибка при отправке: {e}")

if __name__ == "__main__":
    send_email()
