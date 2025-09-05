#!/usr/bin/env python3
import os
import smtplib
from email.mime.text import MIMEText

def test_simple_email():
    from_email = os.environ.get('EMAIL_ADDRESS', '').strip()
    password = os.environ.get('EMAIL_PASSWORD', '')
    to_email = from_email  # Hardcode the same email
    
    print(f"Testing with:")
    print(f"  From: {from_email}")
    print(f"  To: {to_email}")
    print(f"  Same? {from_email == to_email}")
    
    msg = MIMEText("Test from both environments", 'plain', 'utf-8')
    msg['Subject'] = "Test Email"
    msg['From'] = from_email
    msg['To'] = to_email
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, password)
    result = server.sendmail(from_email, [to_email], msg.as_string())
    server.quit()
    
    print(f"✅ Success! Result: {result}")

if __name__ == "__main__":
    test_simple_email()