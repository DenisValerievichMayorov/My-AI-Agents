import imaplib

EMAIL = "denisvalerievichmayorov1@gmail.com"
PASSWORD = "poehpeamrkxpzcfy"
IMAP_SERVER = "imap.gmail.com"

def main():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    
    print("List of all IMAP folders:")
    status, folders = mail.list()
    if status == 'OK':
        for f in folders:
            print(f.decode('utf-8'))
            
    mail.logout()

if __name__ == "__main__":
    main()
