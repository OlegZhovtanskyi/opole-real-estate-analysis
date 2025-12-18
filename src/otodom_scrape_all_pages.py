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
PAGE_DELAY = 3  # seconds between page requests

# =====================================================
# Browser configuration
# =====================================================

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

prefs = {
    "profile.default_content_setting_values.notifications": 2
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 15)

# =====================================================
# Helper functions
# =====================================================

def accept_cookies():
    """Accept cookies popup if present."""
    try:
        button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Akceptuj')]")
            )
        )
        button.click()
        time.sleep(1)
    except TimeoutException:
        pass


def extract_listing_data(listing):
    """
    Extract structured data from a single Otodom listing.
    Returns a dictionary.
    """

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

    # Listing URL (technical ID)
    try:
        data["link"] = listing.find_element(By.TAG_NAME, "a").get_attribute("href")
    except NoSuchElementException:
        pass

    # Price
    try:
        data["price"] = listing.find_element(
            By.CSS_SELECTOR,
            "span[data-sentry-element='MainPrice']"
        ).text
    except NoSuchElementException:
        pass

    # Location
    try:
        data["location"] = listing.find_element(
            By.CSS_SELECTOR,
            "p.css-oxb2ca"
        ).text
    except NoSuchElementException:
        pass

    # Offer type
    try:
        offer_type_span = listing.find_element(
            By.XPATH,
            ".//span[contains(text(), 'Developer') or "
            "contains(text(), 'Biuro nieruchomości') or "
            "contains(text(), 'Oferta prywatna')]"
        )
        data["offer_type"] = offer_type_span.text
    except NoSuchElementException:
        data["offer_type"] = "Developer"

    # Listing details
    spans = listing.find_elements(By.TAG_NAME, "span")

    for span in spans:
        text = span.text.strip()
        if not text:
            continue

        if "zł/m²" in text:
            data["price_per_m2"] = text
        elif "m²" in text and "zł" not in text:
            data["area"] = text
        elif re.search(r"\d+\s*(pokój|pokoje|pokoi)", text.lower()):
            data["rooms"] = text
        elif "piętro" in text.lower() or "parter" in text.lower():
            data["floor"] = text

    return data

# =====================================================
# Main scraping logic
# =====================================================

all_listings_data = []

# Open first page and handle cookies once
driver.get(f"{BASE_URL}?page={START_PAGE}")
accept_cookies()

for page in range(START_PAGE, END_PAGE + 1):
    page_url = f"{BASE_URL}?page={page}"
    driver.get(page_url)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
    listings = driver.find_elements(By.TAG_NAME, "article")

    for listing in listings:
        listing_data = extract_listing_data(listing)
        all_listings_data.append(listing_data)

    time.sleep(PAGE_DELAY)

driver.quit()

# =====================================================
# Save raw dataset
# =====================================================

df = pd.DataFrame(all_listings_data)
df.to_csv("data/raw/opole_listings_raw.csv", index=False)
