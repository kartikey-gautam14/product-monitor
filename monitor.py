#!/usr/bin/env python3
"""
Product Availability Monitor for GitHub Actions
Checks products and sends email notifications when available
"""

import smtplib
import os
import json
import sys
from playwright.sync_api import sync_playwright, TimeoutError
from email.mime.text import MIMEText
from datetime import datetime

def check_product_availability(url: str, pincode: str, pincode_input_selector: str, pincode_select_selector: str, cart_button_selector: str):
    """
    Checks product availability by finding the 'Add to Cart' button and checking if it is enabled.
    """
    with sync_playwright() as p:
        browser = None
        try:
            print("🚀 Launching browser...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            print(f"Navigating to {url}...")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            print(f"✍️ Typing pincode '{pincode}' into input '{pincode_input_selector}'...")
            page.locator(pincode_input_selector).fill(pincode)
            
            print(f"🖱️ Clicking on pincode dropdown element '{pincode_select_selector}'...")
            page.locator(pincode_select_selector).click()
            
            # --- IMPROVED BUTTON CLICKABILITY CHECK ---
            print(f"🧐 Locating the 'Add to Cart' button ('{cart_button_selector}')...")
            
            # First, wait for the button to exist and be visible on the page.
            cart_button = page.locator(cart_button_selector)
            cart_button.wait_for(state="visible", timeout=15000)
            
            # Multi-step check to determine if button is truly clickable
            is_clickable = check_button_clickability(page, cart_button)
            
            if is_clickable:
                print("✅ Product is IN STOCK ('Add to Cart' button is clickable).")
                return True, "In Stock"
            else:
                print("❌ Product is OUT OF STOCK ('Add to Cart' button is not clickable).")
                return False, "Out of Stock"

        except TimeoutError:
            # This error now means the 'Add to Cart' button was not found at all.
            print("❌ CRITICAL ERROR: Could not find the 'Add to Cart' button.", file=sys.stderr)
            print("The website structure may have changed, or the page failed to load properly.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            if browser:
                browser.close()
                print("Browser closed.")

def check_button_clickability(page, button):
    """
    Comprehensive check to determine if a button is truly clickable
    """
    try:
        # Check 1: Traditional disabled attribute
        if not button.is_enabled():
            print("❌ Button is disabled (disabled attribute)")
            return False
        
        # Check 2: Check for disabled-looking CSS classes
        button_classes = button.get_attribute('class') or ""
        disabled_classes = ['disabled', 'inactive', 'not-available', 'sold-out', 'out-of-stock']
        
        for disabled_class in disabled_classes:
            if disabled_class in button_classes.lower():
                print(f"❌ Button has disabled class: {disabled_class}")
                return False
        
        # Check 3: Check opacity (often used to visually disable buttons)
        opacity = page.evaluate("""
            (button) => {
                const style = window.getComputedStyle(button);
                return parseFloat(style.opacity);
            }
        """, button.element_handle())
        
        if opacity < 0.5:  # Very low opacity suggests disabled
            print(f"❌ Button has low opacity: {opacity}")
            return False
        
        # Check 6: Try to check if button is actually clickable by checking pointer events
        pointer_events = page.evaluate("""
            (button) => {
                const style = window.getComputedStyle(button);
                return style.pointerEvents;
            }
        """, button.element_handle())
        
        if pointer_events == 'none':
            print("❌ Button has pointer-events: none")
            return False
        
        # Check 7: Final test - try to hover and see if it responds
        try:
            button.hover(timeout=2000)
            print("✅ Button passed all clickability checks")
            return True
        except:
            print("❌ Button failed hover test")
            return False
            
    except Exception as e:
        print(f"❌ Error checking button clickability: {e}")
        return False


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


def test_gmail_connection():
    """Test Gmail SMTP connection"""
    try:
        from_email = os.environ.get('EMAIL_ADDRESS')
        password = os.environ.get('EMAIL_PASSWORD')
        
        if not from_email or not password:
            return False, "Credentials missing"
            
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(from_email.strip(), password)
        server.quit()
        
        return True, "Connection successful"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def main():
    print("🚀 Starting Product Monitor...")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    # Test before sending
    success, message = test_gmail_connection()
    print(f"Connection test: {message}")
    if success:
        send_email("Test Subject", "Test Body")
    
    # Load previous status
    previous_status = load_previous_status()
    current_status = {}
    
    notifications_sent = 0
    
    is_available, status = check_product_availability(
        url='https://shop.amul.com/en/product/amul-kool-protein-milkshake-or-vanilla-180-ml-or-pack-of-8',
        pincode="560037",
        pincode_input_selector='#search',
        pincode_select_selector='.searchitem-name',
        cart_button_selector='.add-to-cart[title="Add to Cart"]',
    )
    
    current_status["Lassi"] = is_available
    
    # Send notification only if status changed to available
    was_available = previous_status.get("Lassi", False)
    
    if is_available and not was_available:
        print(f"🎉 Lassi became available!")
        
        subject = f"🎉 Amul Lassi is NOW AVAILABLE!"
        body = f"""
🎉 Great news! Your monitored product is now available!

Status: {status}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

🏃‍♂️ Go grab it now!

---
Monitored by GitHub Actions Product Monitor
        """
        print(body)
        if send_email(subject, body):
            notifications_sent += 1
    
    elif is_available and was_available:
        print(f"✅ Lassi still available")
    else:
        print(f"❌ Lassi not available")
    
    # Save current status
    save_status(current_status)
    
    print(f"\n📊 Summary:")
    print(f"   Notifications sent: {notifications_sent}")
    print(f"   Status saved: ✅")
    print("🏁 Monitor completed!")

if __name__ == '__main__':
    main()