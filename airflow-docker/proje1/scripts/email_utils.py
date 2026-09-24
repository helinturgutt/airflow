import smtplib
from email.mime.text import MIMEText

def send_email_notification(subject, body, to_email):
    from_email = "hellinturgut@gmail.com"
    password = "twmusvcudfuphpdf"  # BOŞLUKSUZ ve TIRNAKLI olmalı

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print("✅ E-posta gönderildi.")
    except Exception as e:
        print(f"❌ E-posta gönderilemedi: {e}")
