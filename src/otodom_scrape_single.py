from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# -----------------------------
# Browser configuration
# -----------------------------

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

# Disable browser notification popups
prefs = {
    "profile.default_content_setting_values.notifications": 2
}
options.add_experimental_option("prefs", prefs)

# Initialize WebDriver
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# -----------------------------
# Open Otodom page (Opole)
# -----------------------------

url = "https://www.otodom.pl/pl/oferty/sprzedaz/mieszkanie/opole"
driver.get(url)

wait = WebDriverWait(driver, 15)

# -----------------------------
# Accept cookies if present
# -----------------------------

try:
    cookies_button = wait.until(
    (EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(., 'Akceptuj')]")
    ))
    )
    cookies_button.click()
    print("Cookies accepted")
except TimeoutException:
    print("No cookies popup found")

# -----------------------------
# Wait for listings to load
# -----------------------------

wait.until(
    EC.presence_of_element_located((By.TAG_NAME, "article"))
)
print("Listings loaded")

# -----------------------------
# Extract first listing
# -----------------------------

listing = driver.find_element(By.TAG_NAME, "article")

# Extract price
price = listing.find_element(
    By.CSS_SELECTOR, "span[data-sentry-element='MainPrice']"
).text

# Extract area
area = None

details_spans = listing.find_elements(By.TAG_NAME, "span")

for span in details_spans:
    text = span.text
    if "m²" in span.text and "zł" not in span.text:
        area = text
        break

# -----------------------------
# Output extracted data
# -----------------------------

print("Price:", price)
print("Area:", area)

input("Press ENTER to close browser...")
driver.quit()
