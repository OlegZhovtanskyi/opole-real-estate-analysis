from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

url = "https://www.otodom.pl/pl/oferty/sprzedaz/mieszkanie/opole"
driver.get(url)

# Чекаємо, поки зʼявляться оголошення
WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.TAG_NAME, "article"))
)

print("Strona załadowana")

input("Naciśnij ENTER aby zamknąć przeglądarkę...")
driver.quit()