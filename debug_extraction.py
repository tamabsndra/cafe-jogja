#!/usr/bin/env python3
"""
Debug script untuk menganalisis ekstraksi data cafe
"""

import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

class CafeExtractionDebugger:
    def __init__(self):
        self.setup_driver()

    def setup_driver(self):
        """Setup Chrome driver"""
        options = Options()
        # Don't use headless for debugging
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')

        self.driver = webdriver.Chrome(
            service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
            options=options
        )
        self.wait = WebDriverWait(self.driver, 15)

    def debug_single_cafe(self, query: str = "cafe malioboro yogyakarta"):
        """Debug extraction for a single cafe"""
        print(f"🔍 Debugging: {query}")

        # Go to Google Maps
        self.driver.get('https://maps.google.com')
        time.sleep(3)

        # Search
        search_box = self.wait.until(EC.presence_of_element_located((By.ID, 'searchboxinput')))
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(5)

        # Find cafe elements
        elements = self.driver.find_elements(By.CSS_SELECTOR, '.Nv2PK')
        print(f"📋 Found {len(elements)} elements")

        if elements:
            element = elements[0]  # Take first one
            print("\n" + "="*80)
            print("🔍 DEBUGGING FIRST CAFE ELEMENT")
            print("="*80)

            # Get raw text
            raw_text = element.text
            print(f"📝 Raw text:\n{raw_text}")
            print("\n" + "-"*60)

            # Split into lines
            lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
            print(f"📋 Lines ({len(lines)}):")
            for i, line in enumerate(lines):
                print(f"  {i+1:2d}: '{line}'")

            print("\n" + "-"*60)

            # Debug specific patterns
            self.debug_rating_extraction(lines)
            self.debug_reviews_extraction(lines)
            self.debug_phone_extraction(element)
            self.debug_website_extraction(element)
            self.debug_hours_extraction(lines, element)

            # Click on the cafe for more details
            print("\n🖱️  Clicking on cafe for more details...")
            try:
                element.click()
                time.sleep(3)
                self.debug_detailed_info()
            except Exception as e:
                print(f"❌ Failed to click: {e}")

    def debug_rating_extraction(self, lines):
        """Debug rating extraction"""
        print("🌟 RATING DEBUG:")
        for i, line in enumerate(lines):
            if '⭐' in line or '★' in line or any(char in line for char in ['4.', '3.', '2.', '1.', '5.']):
                print(f"  Line {i+1}: '{line}'")
                rating_match = re.search(r'(\d+[.,]\d*)', line)
                if rating_match:
                    print(f"    ✅ Found rating: {rating_match.group(1)}")
                else:
                    print(f"    ❌ No rating pattern matched")

    def debug_reviews_extraction(self, lines):
        """Debug reviews extraction"""
        print("💬 REVIEWS DEBUG:")
        for i, line in enumerate(lines):
            if '(' in line and ')' in line:
                print(f"  Line {i+1}: '{line}'")
                reviews_match = re.search(r'\(([0-9,.k]+)\)', line)
                if reviews_match:
                    print(f"    ✅ Found reviews: {reviews_match.group(1)}")
                else:
                    print(f"    ❌ No reviews pattern matched")

    def debug_phone_extraction(self, element):
        """Debug phone extraction"""
        print("📞 PHONE DEBUG:")
        try:
            # Try different selectors for phone
            phone_selectors = [

                '[data-value*="phone"]',
                '[data-value*="tel:"]',
                'a[href^="tel:"]',
                '[data-item-id*="phone"]',
                '.rogA2c',  # Common phone class
                'button[data-value*="phone"]',
                '[data-item-id="phone:tel:"]',
                'aria-label="Telepon:"',
            ]

            for selector in phone_selectors:
                phone_elements = element.find_elements(By.CSS_SELECTOR, selector)
                if phone_elements:
                    for phone_elem in phone_elements:
                        text = phone_elem.text.strip()
                        href = phone_elem.get_attribute('href') or ''
                        data_value = phone_elem.get_attribute('data-value') or ''
                        print(f"    Found phone element - Text: '{text}', Href: '{href}', Data: '{data_value}'")

            # Also check in text for phone patterns
            full_text = element.text
            phone_patterns = [
                r'\+62[\d\s-]+',
                r'0[\d\s-]{8,}',
                r'\(\d+\)\s*\d+',
                r'\d{3,4}[-\s]\d{3,4}[-\s]\d{3,4}'
            ]

            for pattern in phone_patterns:
                matches = re.findall(pattern, full_text)
                if matches:
                    print(f"    Found phone pattern '{pattern}': {matches}")

        except Exception as e:
            print(f"    ❌ Phone debug error: {e}")

    def debug_website_extraction(self, element):
        """Debug website extraction"""
        print("🌐 WEBSITE DEBUG:")
        try:
            # Try different selectors for website
            website_selectors = [
                'a[href^="http"]',
                '[data-value^="http"]',
                'button[data-value^="http"]',
                '.CsEnBe',  # Common website class
                'a[data-item-id*="authority"]',
                'a[class="CsEnBe"]'
            ]

            for selector in website_selectors:
                website_elements = element.find_elements(By.CSS_SELECTOR, selector)
                if website_elements:
                    for web_elem in website_elements:
                        text = web_elem.text.strip()
                        href = web_elem.get_attribute('href') or ''
                        data_value = web_elem.get_attribute('data-value') or ''
                        print(f"    Found website element - Text: '{text}', Href: '{href}', Data: '{data_value}'")

        except Exception as e:
            print(f"    ❌ Website debug error: {e}")

    def debug_hours_extraction(self, lines, element):
        """Debug opening hours extraction"""
        print("🕐 HOURS DEBUG:")
        for i, line in enumerate(lines):
            if any(word in line.lower() for word in ['buka', 'tutup', 'jam', 'open', 'close', 'hours']):
                print(f"  Line {i+1}: '{line}'")

        # Also try to find hours in detailed view
        try:
            hours_elements = element.find_elements(By.CSS_SELECTOR, '[data-item-id*="oh"]')
            for hours_elem in hours_elements:
                print(f"    Hours element: '{hours_elem.text}'")
        except Exception as e:
            print(f"    ❌ Hours debug error: {e}")

    def debug_detailed_info(self):
        """Debug detailed info after clicking on cafe"""
        print("\n📋 DETAILED INFO DEBUG:")
        time.sleep(2)

        # Address
        try:
            addr_btn = self.driver.find_element(By.CSS_SELECTOR, 'button.CsEnBe[data-item-id="address"] .Io6YTe')
            print(f"📍 Address: {addr_btn.text.strip()}")
        except Exception:
            print("📍 Address: -")

        # Website
        try:
            website_link = self.driver.find_element(By.CSS_SELECTOR, 'a.CsEnBe[data-item-id*="authority"]')
            print(f"🌐 Website: {website_link.get_attribute('href')}")
        except Exception:
            print("🌐 Website: -")

        # Phone
        try:
            phone_btn = self.driver.find_element(By.CSS_SELECTOR, 'button.CsEnBe[data-item-id^="phone:tel:"]')
            aria = phone_btn.get_attribute('aria-label') or ''
            text = phone_btn.text.strip()
            tel_link = ''
            try:
                tel_a = self.driver.find_element(By.CSS_SELECTOR, 'a[href^="tel:"]')
                tel_link = tel_a.get_attribute('href')
            except Exception:
                pass
            print(f"📞 Phone: text='{text}', aria='{aria}', tel='{tel_link}'")
        except Exception:
            print("📞 Phone: -")

        # Opening hours (weekly table)
        try:
            # Expand hours dropdown if present
            try:
                toggle = self.driver.find_element(By.CSS_SELECTOR, 'div.OMl5r[role="button"]')
                if toggle.get_attribute('aria-expanded') == 'false':
                    toggle.click()
                    time.sleep(1)
            except Exception:
                pass

            rows = self.driver.find_elements(By.CSS_SELECTOR, 'table.eK4R0e tr.y0skZc')
            if rows:
                print("🕐 Weekly hours:")
                for row in rows:
                    try:
                        day = row.find_element(By.CSS_SELECTOR, 'td.ylH6lf').text.strip()
                        hours = row.find_element(By.CSS_SELECTOR, 'td.mxowUb').text.strip()
                        print(f"   - {day}: {hours}")
                    except Exception:
                        continue
            else:
                print("🕐 Weekly hours: -")
        except Exception as e:
            print(f"🕐 Weekly hours error: {e}")

        # Price range per person summary and histogram
        try:
            try:
                price_btn = self.driver.find_element(By.CSS_SELECTOR, 'div.MNVeJb[role="button"]')
                print(f"💲 Price summary: {price_btn.text.strip()}")
            except Exception:
                print("💲 Price summary: -")

            hist_rows = self.driver.find_elements(By.CSS_SELECTOR, 'table.rqRH4d tr[data-item-id]')
            if hist_rows:
                print("💲 Price histogram:")
                for r in hist_rows:
                    try:
                        label = r.find_element(By.CSS_SELECTOR, 'td.fsAi0e').text.strip()
                        percent = r.find_element(By.CSS_SELECTOR, 'span.QANbtc').get_attribute('aria-label')
                        print(f"   - {label}: {percent}")
                    except Exception:
                        continue
            else:
                print("💲 Price histogram: -")
        except Exception as e:
            print(f"💲 Price error: {e}")

        # Legacy details retained
        try:
            phone_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="phone"]')
            print(f"📞 Phone button (legacy) found: {phone_button.get_attribute('data-value')}")
        except:
            print("📞 No legacy phone button found")

        try:
            rating_elem = self.driver.find_element(By.CSS_SELECTOR, '.F7nice')
            print(f"🌟 Rating in detail: {rating_elem.text}")
        except:
            print("🌟 No rating in detail view")

    def cleanup(self):
        """Close driver"""
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    debugger = CafeExtractionDebugger()

    try:
        debugger.debug_single_cafe("cafe malioboro yogyakarta")

        print("\n" + "="*80)
        print("Debug completed. Press Enter to close browser...")
        input()

    finally:
        debugger.cleanup()
