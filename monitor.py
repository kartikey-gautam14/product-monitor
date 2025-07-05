#!/usr/bin/env python3
"""
Product Availability Monitor for GitHub Actions
Checks products and sends email notifications when available
"""

import requests
import smtplib
import os
import json
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from datetime import datetime

def check_product(url, selector, keywords):
    """Check if product is available"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"Checking: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        element = soup.select_one(selector)
        
        if not element:
            print(f"❌ Element not found with selector: {selector}")
            return False, "Element not found"
            
        text = element.get_text().strip().lower()
        print(f"Found text: {text[:100]}...")
        
        # Check if any available keywords are present
        for keyword in keywords:
            if keyword.lower() in text:
                print(f"✅ Found keyword: {keyword}")
                return True, f"Found: {keyword}"
                
        print(f"❌ No availability keywords found")
        return False, f"Current status: {text[:50]}..."
        
    except Exception as e:
        print(f"❌ Error checking {url}: {str(e)}")
        return False, f"Error: {str(e)}"

def send_email(subject, body):
    """Send email notification using Gmail"""
    try:
        from_email = os.environ.get('EMAIL_ADDRESS')
        password = os.environ.get('EMAIL_PASSWORD')
        to_email = os.environ.get('TO_EMAIL', from_email)  # Default to same email
        
        if not from_email or not password:
            print("❌ Email credentials not configured")
            return False
            
        print(f"📧 Sending email to: {to_email}")
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        # Use Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()
        
        print("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        return False

def load_previous_status():
    """Load previous status from file (if exists)"""
    try:
        if os.path.exists('status.json'):
            with open('status.json', 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_status(status_data):
    """Save current status to file"""
    try:
        with open('status.json', 'w') as f:
            json.dump(status_data, f)
    except Exception as e:
        print(f"❌ Error saving status: {str(e)}")

def main():
    print("🚀 Starting Product Monitor...")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Load previous status
    previous_status = load_previous_status()
    current_status = {}
    
    # Configure your products here
    products = [
        {
            'name': 'iPhone 15 Pro',
            'url': 'https://www.apple.com/iphone-15-pro/',
            'selector': '.rf-pdp-buybox',  # Apple's buy box
            'keywords': ['buy', 'add to bag', 'available']
        },
        {
            'name': 'PlayStation 5',
            'url': 'https://www.bestbuy.com/site/sony-playstation-5-console/6426149.p',
            'selector': '.fulfillment-add-to-cart-button',
            'keywords': ['add to cart', 'available']
        }
        # Add more products here following the same pattern
    ]
    
    notifications_sent = 0
    
    for i, product in enumerate(products):
        print(f"\n📦 Checking product {i+1}/{len(products)}: {product['name']}")
        
        is_available, status = check_product(
            product['url'], 
            product['selector'], 
            product['keywords']
        )
        
        product_key = f"{product['name']}-{product['url']}"
        current_status[product_key] = is_available
        
        # Send notification only if status changed to available
        was_available = previous_status.get(product_key, False)
        
        if is_available and not was_available:
            print(f"🎉 {product['name']} became available!")
            
            subject = f"🎉 {product['name']} is NOW AVAILABLE!"
            body = f"""
🎉 Great news! Your monitored product is now available!

Product: {product['name']}
Status: {status}
URL: {product['url']}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

🏃‍♂️ Go grab it now!

---
Monitored by GitHub Actions Product Monitor
            """
            
            if send_email(subject, body):
                notifications_sent += 1
        
        elif is_available and was_available:
            print(f"✅ {product['name']} still available")
        else:
            print(f"❌ {product['name']} not available")
    
    # Save current status
    save_status(current_status)
    
    print(f"\n📊 Summary:")
    print(f"   Products checked: {len(products)}")
    print(f"   Notifications sent: {notifications_sent}")
    print(f"   Status saved: ✅")
    print("🏁 Monitor completed!")

if __name__ == '__main__':
    main()