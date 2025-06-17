import unittest
import sys
import os

# 👇 Allow Python to find app.py and database.py in parent folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
import database

# ---------- TEST 1: Flask route ----------
class TestAppRoutes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_home_page_loads(self):
        """Checks if the home page (login screen) loads successfully."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


# ---------- TEST 2: Skip database connection ----------
class TestDatabase(unittest.TestCase):
    def test_skip_db(self):
        """Skips the DB test since no access to DTU MySQL server."""
        self.skipTest("Skipping DB test – no access to MySQL server.")


# ---------- TEST 3: CPR validation logic ----------
def is_valid_cpr(cpr: str) -> bool:
    """
    Returns True if CPR is exactly 10 digits.
    CPR format: DDMMYYXXXX (only digits, no dashes)
    """
    return cpr.isdigit() and len(cpr) == 10

class TestCPRValidation(unittest.TestCase):
    def test_valid_cpr(self):
        """Tests valid and invalid CPR formats."""
        self.assertTrue(is_valid_cpr("1234567890"))        # valid
        self.assertFalse(is_valid_cpr("abcd123456"))       # contains letters
        self.assertFalse(is_valid_cpr("12345678"))         # too short
        self.assertFalse(is_valid_cpr("123456789012"))     # too long
        self.assertFalse(is_valid_cpr("123456-7890"))      # has dash


# ---------- Run tests ----------
if __name__ == '__main__':
    unittest.main()
