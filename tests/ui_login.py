import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

class AuthTests(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        self.driver.get('http://127.0.0.1:5000')  # Update with your app's URL

    def tearDown(self):
        self.driver.quit()

    def test_register(self):
        driver = self.driver
        driver.get('http://127.0.0.1:5000/auth/register')  # Update with your register URL
        
        driver.find_element(By.NAME, 'username').send_keys('testuser')
        driver.find_element(By.NAME, 'password').send_keys('password123')
        driver.find_element(By.NAME, 'confirm').send_keys('password123')
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        success_message = driver.find_element(By.CLASS_NAME, 'alert-success').text
        self.assertIn('Registration successful', success_message)

    def test_login(self):
        driver = self.driver
        driver.get('http://127.0.0.1:5000/auth/login')  # Update with your login URL

        driver.find_element(By.NAME, 'username').send_keys('testuser')
        driver.find_element(By.NAME, 'password').send_keys('password123')
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        welcome_message = driver.find_element(By.TAG_NAME, 'h1').text
        self.assertIn('Welcome', welcome_message)

    def test_logout(self):
        driver = self.driver
        self.test_login()  # First, log in
        driver.find_element(By.LINK_TEXT, 'Logout').click()  # Update the selector if necessary

        logout_message = driver.find_element(By.CLASS_NAME, 'alert-info').text
        self.assertIn('You have been logged out', logout_message)

if __name__ == '__main__':
    unittest.main()
