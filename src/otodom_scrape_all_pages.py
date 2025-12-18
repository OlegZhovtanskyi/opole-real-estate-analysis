import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# =====================================================
# Configuration
# =====================================================

BASE_URL = "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/opolskie/opole/opole/opole"
START_PAGE = 1
END_PAGE = 15

# =====================================================
# Browser configuration
# =====================================================

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

# Disable notifications
prefs = {
    "profile.default_content_setting_values.notifications": 2
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# =====================================================
# Helper functions
# =====================================================

def accept_cookies(driver, wait):
    """Accept cookies popup if present."""
    try:
        cookies_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Akceptuj')]")
            )
        )
        cookies_button.click()
        print("  ✓ Cookies accepted")
        time.sleep(1)
        return True
    except TimeoutException:
        print("  ℹ No cookies popup found")
        return False


def extract_listing_data(listing):
    """Extract structured data from a single Otodom listing."""
    
    data = {
        "link": None,
        "price": None,
        "location": None,
        "area": None,
        "price_per_m2": None,
        "rooms": None,
        "floor": None,
        "offer_type": None
    }

    try:
        # Listing URL
        data["link"] = listing.find_element(By.TAG_NAME, "a").get_attribute("href")
    except NoSuchElementException:
        pass

    try:
        # Price
        data["price"] = listing.find_element(
            By.CSS_SELECTOR,
            "span[data-sentry-element='MainPrice']"
        ).text
    except NoSuchElementException:
        pass

    try:
        # Location
        data["location"] = listing.find_element(
            By.CSS_SELECTOR,
            "p.css-oxb2ca"
        ).text
    except NoSuchElementException:
        pass

    try:
        # Offer type
        offer_type_span = listing.find_element(
            By.XPATH,
            ".//span[contains(text(), 'Developer') or "
            "contains(text(), 'Biuro nieruchomości') or "
            "contains(text(), 'Oferta prywatna')]"
        )
        data["offer_type"] = offer_type_span.text
    except NoSuchElementException:
        data["offer_type"] = "Developer"

    # Extract listing details
    spans = listing.find_elements(By.TAG_NAME, "span")

    for span in spans:
        text = span.text.strip()

        if not text:
            continue

        if "zł/m²" in text:
            data["price_per_m2"] = text
        elif "m²" in text and "zł" not in text:
            data["area"] = text
        elif re.search(r'\d+\s*(pokój|pokoje|pokoi)', text.lower()):
            data["rooms"] = text
        elif "piętro" in text.lower() or "parter" in text.lower():
            data["floor"] = text

    return data


def scrape_page(driver, page_num, base_url):
    """Scrape a single page and return listing data."""
    
    page_url = f"{base_url}?page={page_num}"
    print(f"\n{'='*60}")
    print(f"Processing page {page_num}")
    print(f"URL: {page_url}")
    print(f"{'='*60}")
    
    try:
        driver.get(page_url)
        
        # Shorter wait for subsequent elements
        wait = WebDriverWait(driver, 10)
        
        # Wait for listings to appear
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
        
        # Small delay to ensure page is fully loaded
        time.sleep(2)
        
        # Find all listings
        listings = driver.find_elements(By.TAG_NAME, "article")
        print(f"  ✓ Found {len(listings)} listings")
        
        # Extract data from each listing
        page_data = []
        for idx, listing in enumerate(listings, 1):
            try:
                listing_data = extract_listing_data(listing)
                page_data.append(listing_data)
            except Exception as e:
                print(f"  ⚠ Error extracting listing {idx}: {e}")
                continue
        
        print(f"  ✓ Successfully extracted {len(page_data)} listings")
        return page_data
        
    except TimeoutException:
        print(f"  ✗ Timeout on page {page_num} - page may not exist or is slow to load")
        return []
    except Exception as e:
        print(f"  ✗ Error on page {page_num}: {e}")
        return []


# =====================================================
# Main scraping loop
# =====================================================

all_listings_data = []

try:
    print("\n" + "="*60)
    print("Starting Otodom scraper")
    print("="*60)
    
    # Accept cookies on first page
    driver.get(BASE_URL + "?page=1")
    wait = WebDriverWait(driver, 15)
    accept_cookies(driver, wait)
    
    # Scrape all pages
    for page in range(START_PAGE, END_PAGE + 1):
        page_data = scrape_page(driver, page, BASE_URL)
        all_listings_data.extend(page_data)
        
        # Add delay between pages to avoid rate limiting
        if page < END_PAGE:
            delay = 3
            print(f"  ⏳ Waiting {delay}s before next page...")
            time.sleep(delay)
    
    # =====================================================
    # Save results
    # =====================================================
    
    print("\n" + "="*60)
    print("Saving results...")
    print("="*60)
    
    df = pd.DataFrame(all_listings_data)
    df.to_csv("data/raw/opole_listings_raw.csv", index=False)
    
    print(f"\n✓ Successfully saved {len(df)} listings to opole_listings_raw.csv")
    print(f"\nBreakdown:")
    print(f"  - Total pages processed: {END_PAGE - START_PAGE + 1}")
    print(f"  - Total listings found: {len(df)}")
    print(f"  - Average per page: {len(df) / (END_PAGE - START_PAGE + 1):.1f}")

except KeyboardInterrupt:
    print("\n\n⚠ Scraping interrupted by user")
    print(f"Saving {len(all_listings_data)} listings collected so far...")
    
    if all_listings_data:
        df = pd.DataFrame(all_listings_data)
        df.to_csv("data/raw/opole_listings_raw_partial.csv", index=False)
        print(f"✓ Partial results saved to opole_listings_raw_partial.csv")

except Exception as e:
    print(f"\n\n✗ Fatal error: {e}")
    
finally:
    print("\n" + "="*60)
    print("Closing browser...")
    print("="*60)
    driver.quit()
    print("✓ Done")