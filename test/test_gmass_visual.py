#!/usr/bin/env python3
"""
Visual test of GMass scraper - opens browser in visible mode
"""

import time
import re
import urllib.parse
from datetime import datetime
from playwright.sync_api import sync_playwright

def test_gmass_visual_scraping():
    """Test GMass scraper with visible browser"""
    print("Testing GMass scraper with visible browser...")
    print("This will open a browser window so you can see the scraping in action.")
    
    test_email = "test@example.com"
    
    try:
        with sync_playwright() as p:
            # Launch browser in non-headless mode (visible)
            browser = p.chromium.launch(headless=False, slow_mo=1000)  # slow_mo makes actions slower for visibility
            context = browser.new_context()
            page = context.new_page()
            
            print(f"Opening GMass page for: {test_email}")
            encoded_email = urllib.parse.quote(test_email)
            url = f"https://www.gmass.co/inbox?q={encoded_email}"
            
            print(f"Navigating to: {url}")
            page.goto(url, wait_until='domcontentloaded', timeout=15000)
            
            print("Waiting for page to load completely...")
            time.sleep(5)  # Wait for dynamic content
            
            # Get page content for analysis
            page_content = page.content().lower()
            print("Analyzing page content...")
            
            # Look for text content containing placement info
            inbox_count = promotions_count = spam_count = 0
            
            # Simple text parsing approach
            if 'inbox' in page_content:
                inbox_matches = re.findall(r'inbox.*?(\d+)', page_content)
                if inbox_matches:
                    inbox_count = int(inbox_matches[0])
                    print(f"Found inbox count: {inbox_count}")
            
            if 'promotions' in page_content:
                promo_matches = re.findall(r'promotions.*?(\d+)', page_content)
                if promo_matches:
                    promotions_count = int(promo_matches[0])
                    print(f"Found promotions count: {promotions_count}")
            
            if 'spam' in page_content:
                spam_matches = re.findall(r'spam.*?(\d+)', page_content)
                if spam_matches:
                    spam_count = int(spam_matches[0])
                    print(f"Found spam count: {spam_count}")
            
            # Calculate score
            score = inbox_count + (0.6 * promotions_count)
            
            result = {
                "sender": test_email,
                "inbox": inbox_count,
                "promotions": promotions_count,
                "spam": spam_count,
                "score": round(score, 1),
                "link": url,
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            
            print("\nScraping Results:")
            print("=" * 30)
            print(f"Email: {result['sender']}")
            print(f"Inbox: {result['inbox']}")
            print(f"Promotions: {result['promotions']}")
            print(f"Spam: {result['spam']}")
            print(f"Score: {result['score']}")
            print(f"Timestamp: {result['ts']}")
            
            print("\nBrowser will close in 10 seconds...")
            time.sleep(10)
            
            browser.close()
            return result
            
    except Exception as e:
        print(f"Error during visual test: {e}")
        return None

if __name__ == "__main__":
    result = test_gmass_visual_scraping()
    if result:
        print("\nVisual test completed successfully!")
    else:
        print("\nVisual test failed!")