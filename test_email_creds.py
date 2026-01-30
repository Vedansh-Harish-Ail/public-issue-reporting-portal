import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def test_email():
    # Check env vars
    env_user = os.environ.get("MAIL_USERNAME")
    env_pass = os.environ.get("MAIL_PASSWORD")
    
    print(f"Environment MAIL_USERNAME: {env_user}")
    print(f"Environment MAIL_PASSWORD: {'***' if env_pass else 'None'}")

    # Use defaults if not set, just like app.py
    sender_email = env_user or "panchayatseva1@gmail.com"
    app_password = env_pass or "tkao zyic hwog dxnd"
    
    print(f"Attempting to send with user: {sender_email}")
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = sender_email # Loopback test
        msg['Subject'] = "Test Email from Script"
        body = "If you see this, email sending is working."
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, sender_email, msg.as_string())
        server.quit()
        print("Email Sent DATE RECV: SUCCESS!")
        
    except Exception as e:
        print(f"Email Send FAILED: {e}")

if __name__ == "__main__":
    test_email()
