from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure Chrome browser options
options = webdriver.ChromeOptions()
# Start browser in maximized window mode
options.add_argument("--start-maximized")

# Initialize Chrome webdriver with automatic ChromeDriver installation
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# Target URL - Otodom property listings in Opole
url = "https://www.otodom.pl/pl/oferty/sprzedaz/mieszkanie/opole"
driver.get(url)

# Wait up to 15 seconds for property listings (article elements) to appear on the page
# This ensures the page is fully loaded before proceeding
WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.TAG_NAME, "article"))
)

print("Strona załadowana")

# Pause execution until user presses ENTER - keeps browser open for inspection
input("Naciśnij ENTER aby zamknąć przeglądarkę...")
# Close browser and end webdriver session
driver.quit()