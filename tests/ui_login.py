import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

class AuthTests(unittest.TestCase):

    def setUp(self):
        chrome_options = Options()
        # Uncomment this line if you want to see the browser UI during tests
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--remote-debugging-port=9222")

        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        self.driver.get("http://127.0.0.1:5000")

    def tearDown(self):
        self.driver.quit()

    def test_register(self):
        driver = self.driver
        driver.find_element(By.LINK_TEXT, "Register").click()

        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")
        confirm_input = driver.find_element(By.NAME, "confirm")
        submit_button = driver.find_element(By.TAG_NAME, "button")

        username_input.send_keys("testuser")
        password_input.send_keys("testpassword")
        confirm_input.send_keys("testpassword")
        submit_button.click()

        # Check for success message
        success_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-success'))
        ).text
        self.assertIn('Registration successful', success_message)

    def test_login(self):
        driver = self.driver
        driver.find_element(By.LINK_TEXT, "Login").click()

        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")
        submit_button = driver.find_element(By.TAG_NAME, "button")

        username_input.send_keys("testuser")
        password_input.send_keys("testpassword")
        submit_button.click()

        # Check for welcome message
        welcome_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        ).text
        self.assertIn('Welcome', welcome_message)

    def test_logout(self):
        driver = self.driver
        self.test_login()  # First, log in

        driver.find_element(By.LINK_TEXT, "Logout").click()

        # Check for login message
        login_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        ).text
        self.assertIn('Login', login_message)

if __name__ == "__main__":
    unittest.main()
