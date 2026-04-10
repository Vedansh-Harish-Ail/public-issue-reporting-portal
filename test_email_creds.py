import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from email_templates import EMAIL_TEMPLATES

# Load environment variables
load_dotenv()

def test_email():
    sender_email = os.environ.get("MAIL_USERNAME")
    app_password = os.environ.get("MAIL_PASSWORD")
    
    if not sender_email or not app_password:
        print("FAILED: MAIL_USERNAME or MAIL_PASSWORD environment variables are not set.")
        print("Create a .env file with these values or set them in your environment.")
        return
    recipient1 = "kshamyaamin19@gmail.com"
    recipient2 = "ailvedansh@gmail.com"
    otp_code = "123456"
    
    # Use the template from the new file
    html_template = EMAIL_TEMPLATES["en"].format(otp_code)

    recipients = [recipient1, recipient2]
    print(f"Attempting to send HTML OTP to: {', '.join(recipients)}")
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = "Meri Panchayat: Testing  OTP"
        msg.attach(MIMEText(html_template, 'html', 'utf-8'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipients, msg.as_string())
        server.quit()
        print("--- DEBUG: FIRST 300 CHARS OF EMAIL STRING ---")
        print(msg.as_string()[:300])
        print("--- END DEBUG ---")
        print(f"SUCCESS! Check your inbox at {', '.join(recipients)}")
        
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_email()
