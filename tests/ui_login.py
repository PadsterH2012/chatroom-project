import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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

    def test_register(self):
        self.driver.get("http://localhost:5000/auth/register")
        username_field = self.driver.find_element(By.NAME, "username")
        password_field = self.driver.find_element(By.NAME, "password")
        confirm_field = self.driver.find_element(By.NAME, "confirm")
        register_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

        username_field.send_keys("testuser")
        password_field.send_keys("password")
        confirm_field.send_keys("password")
        register_button.click()

        # Check if registration was successful by finding a specific element
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))

    def test_login(self):
        self.driver.get("http://localhost:5000/auth/login")
        
        # Verify we are on the login page
        print(f"Current URL before login: {self.driver.current_url}")
        print(f"Page source before login:\n{self.driver.page_source}")

        username_field = self.driver.find_element(By.NAME, "username")
        password_field = self.driver.find_element(By.NAME, "password")
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

        username_field.send_keys("testuser")
        password_field.send_keys("password")
        login_button.click()

        # Wait for a potential redirect or error message
        WebDriverWait(self.driver, 10).until(EC.url_changes("http://localhost:5000/auth/login"))

        # Debug print to check current URL and page source after login attempt
        print(f"Current URL after login: {self.driver.current_url}")
        print(f"Page source after login:\n{self.driver.page_source}")

        # Check for common error messages
        error_message = self.driver.find_elements(By.CLASS_NAME, "error-message")
        if error_message:
            print(f"Error message found: {error_message[0].text}")

        # Explicitly wait for the "Project Room" text to appear after login
        WebDriverWait(self.driver, 10).until(EC.text_to_be_present_in_element((By.TAG_NAME, "h1"), "Project Room"))

        # Check if login was successful by verifying the presence of "Project Room"
        self.assertIn("Project Room", self.driver.page_source)

if __name__ == "__main__":
    unittest.main()
