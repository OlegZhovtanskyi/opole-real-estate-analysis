from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

# =====================================================
# Browser configuration
# =====================================================

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

# Disable browser notification popups
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
# Open Otodom page (Opole – apartments for sale)
# =====================================================

driver.get("https://www.otodom.pl/pl/oferty/sprzedaz/mieszkanie/opole")

# =====================================================
# Accept cookies (robust, text-based selector)
# =====================================================

try:
    cookies_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(., 'Akceptuj')]")
        )
    )
    cookies_button.click()
except TimeoutException:
    # Cookies popup not present
    pass

# =====================================================
# Wait for listings to load
# =====================================================

wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
listings = driver.find_elements(By.TAG_NAME, "article")

# =====================================================
# Listing data extraction function
# =====================================================

def extract_listing_data(listing):
    """
    Extract structured data from a single Otodom listing.

    Returns:
        dict: listing data (price, area, rooms, etc.)
    """

    data = {
        "price": None,
        "location": None,
        "area": None,
        "price_per_m2": None,
        "rooms": None,
        "floor": None,
        "offer_type": None
    }

    # -----------------------------
    # Price
    # -----------------------------
    try:
        data["price"] = listing.find_element(
            By.CSS_SELECTOR,
            "span[data-sentry-element='MainPrice']"
        ).text
    except NoSuchElementException:
        pass

    # -----------------------------
    # Location
    # -----------------------------
    try:
        data["location"] = listing.find_element(
            By.CSS_SELECTOR,
            "p.css-oxb2ca"
        ).text
    except NoSuchElementException:
        pass

    # -----------------------------
    # Offer type (Developer / Agency / Private)
    # -----------------------------
    try:
        offer_type_span = listing.find_element(
            By.XPATH,
            ".//span[contains(text(), 'Developer') or "
            "contains(text(), 'Biuro nieruchomości') or "
            "contains(text(), 'Oferta prywatna')]"
        )
        data["offer_type"] = offer_type_span.text
    except NoSuchElementException:
        # If not explicitly stated, assume developer offer
        data["offer_type"] = "Developer"

    # -----------------------------
    # Listing details (area, price per m², rooms, floor)
    # -----------------------------
    spans = listing.find_elements(By.TAG_NAME, "span")

    for span in spans:
        text = span.text.strip()

        if not text:
            continue

        # Price per square meter
        if "zł/m²" in text:
            data["price_per_m2"] = text

        # Area (exclude price per m²)
        elif "m²" in text and "zł" not in text:
            data["area"] = text

        # Number of rooms (pokój / pokoje / pokoi)
        elif re.search(r'\d+\s*(pokój|pokoje|pokoi)', text.lower()):
            data["rooms"] = text

        # Floor (piętro / parter)
        elif "piętro" in text.lower() or "parter" in text.lower():
            data["floor"] = text

    return data

# =====================================================
# Extract data from all listings on the page
# =====================================================

all_listings_data = []

for idx, listing in enumerate(listings, 1):
    listing_data = extract_listing_data(listing)
    all_listings_data.append(listing_data)

    # Print first 7 listings for manual verification
    if idx <= 7:
        print(f"--- Listing {idx} ---")
        for key, value in listing_data.items():
            print(f"{key}: {value}")
        print()

print(f"\nTotal listings collected: {len(all_listings_data)}")
