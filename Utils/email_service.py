import smtplib
from email.mime.text import MIMEText
from config import Config

def send_otp_email(to_email, otp):
    msg = MIMEText(f"Your OTP is: {otp}")
    msg["Subject"] = "Login OTP Verification"
    msg["From"] = Config.EMAIL_USER
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(Config.EMAIL_USER, Config.EMAIL_PASS)
    server.send_message(msg)
    server.quit()
