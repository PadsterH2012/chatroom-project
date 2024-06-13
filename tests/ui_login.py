import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

class UITest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        options = Options()
        options.binary_location = "/usr/bin/google-chrome"  # Specify the path to the Chrome binary
        options.headless = True
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        cls.driver.implicitly_wait(10)
        cls.driver.maximize_window()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_load_page(self):
        self.driver.get("http://localhost:5000/")
        self.assertIn("Home", self.driver.title)

    def test_login(self):
        self.driver.get("http://localhost:5000/auth/login")
        username_field = self.driver.find_element(By.NAME, "username")
        password_field = self.driver.find_element(By.NAME, "password")
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

        username_field.send_keys("testuser")
        password_field.send_keys("password")
        login_button.click()

        self.assertTrue(self.driver.find_element(By.ID, "logout").is_displayed())

if __name__ == "__main__":
    unittest.main()
