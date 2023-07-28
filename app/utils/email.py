import smtplib
import ssl
from email.message import EmailMessage

from app.config import SMTP_PASSWORD, SMTP_USERNAME


# Setup Email Service
def send_email(to_email, subject, message):
    msg = EmailMessage()
    msg['From'] = SMTP_USERNAME
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(message)

     # Add SSL (layer of security)
    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False
