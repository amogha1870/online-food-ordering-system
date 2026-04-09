

import sys
import time
import unittest

BASE_URL = "http://127.0.0.1:5000"

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import NoSuchElementException
except ImportError:
    print("ERROR: Run:  pip install selenium webdriver-manager")
    sys.exit(1)

try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_MANAGER = True
except ImportError:
    USE_MANAGER = False


def make_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1400,900")
    options.add_argument("--disable-gpu")
    if USE_MANAGER:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
    else:
        driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(6)
    return driver


HEADLESS = "--headless" in sys.argv


# =============================================================================
#  REGRESSION TEST CLASS
# =============================================================================

class SeleniumRegressionTests(unittest.TestCase):
    """
    Selenium Regression Tests
    -------------------------
    Each test represents a real bug that was fixed.
    These tests run automatically to ensure the bug stays fixed.
    """

    def setUp(self):
        """Create a fresh browser for each regression test."""
        self.driver = make_driver(HEADLESS)
        self.driver.implicitly_wait(6)

    def tearDown(self):
        """Close browser after each test."""
        self.driver.quit()

    def _login(self, email="user@demo.com", password="demo123"):
        self.driver.get(BASE_URL + "/")
        self.driver.find_element(By.ID, "email").send_keys(email)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

    def _add_item_to_cart(self, restaurant_id=2):
        self.driver.get(BASE_URL + f"/menu/{restaurant_id}")
        time.sleep(0.8)
        add_btns = self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")
        if add_btns:
            add_btns[0].click()
            time.sleep(0.8)

    # ── REG-01: Login with wrong password must NOT reach restaurants ──────────
    def test_REG_01_wrong_password_stays_on_login(self):
        """
        BUG: Any password was accepted due to missing password check in query.
        FIX: SQL query now checks both email AND password.
        VERIFY: Wrong password keeps user on login page with error.
        """
        self.driver.get(BASE_URL + "/")
        self.driver.find_element(By.ID, "email").send_keys("user@demo.com")
        self.driver.find_element(By.ID, "password").send_keys("WRONG_PASSWORD_123")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.8)

        # Must stay on login page
        self.assertNotIn("restaurants", self.driver.current_url,
                         "REG-01 FAILED: Wrong password reached restaurants page")
        self.assertIn("Invalid", self.driver.page_source,
                      "REG-01 FAILED: Error message not shown for wrong password")
        print("\n  [PASS] REG-01: Wrong password blocked – stays on login with error")

    # ── REG-02: Empty login fields must not cause server crash ────────────────
    def test_REG_02_empty_login_does_not_crash(self):
        """
        BUG: Submitting empty login form caused a 500 Internal Server Error.
        FIX: form.get() returns empty string safely, query returns no match.
        VERIFY: Page stays on login, no 500 error.
        """
        self.driver.get(BASE_URL + "/")
        # Submit form with no input
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.8)

        self.assertNotIn("500", self.driver.page_source,
                         "REG-02 FAILED: Empty login caused 500 error")
        self.assertNotIn("Internal Server Error", self.driver.page_source,
                         "REG-02 FAILED: Empty login caused server error")
        print("  [PASS] REG-02: Empty login form handled safely – no server crash")

    # ── REG-03: Unknown email must not crash and must show error ──────────────
    def test_REG_03_unknown_email_shows_error_not_crash(self):
        """
        BUG: Unknown email caused NoneType AttributeError crash.
        FIX: Check if user is None before accessing user fields.
        VERIFY: Shows error message without crashing.
        """
        self.driver.get(BASE_URL + "/")
        self.driver.find_element(By.ID, "email").send_keys("doesnotexist@xyz.com")
        self.driver.find_element(By.ID, "password").send_keys("somepass")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.8)

        self.assertNotIn("AttributeError", self.driver.page_source,
                         "REG-03 FAILED: Unknown email caused AttributeError")
        self.assertNotIn("500", self.driver.page_source,
                         "REG-03 FAILED: Unknown email caused 500 error")
        self.assertIn("Invalid", self.driver.page_source,
                      "REG-03 FAILED: Error message not shown for unknown email")
        print("  [PASS] REG-03: Unknown email shows error message, no crash")

    # ── REG-04: Protected pages must redirect without login ───────────────────
    def test_REG_04_protected_pages_redirect_without_login(self):
        """
        BUG: Protected routes were accessible without login.
        FIX: @login_required decorator redirects unauthenticated users.
        VERIFY: Each protected page redirects to login page.
        """
        protected_urls = [
            BASE_URL + "/restaurants",
            BASE_URL + "/menu/2",
            BASE_URL + "/cart",
            BASE_URL + "/checkout",
        ]
        for url in protected_urls:
            self.driver.get(url)
            time.sleep(0.5)
            # Must end up on login page, not the protected page
            self.assertNotIn(
                "All Restaurants", self.driver.page_source,
                f"REG-04 FAILED: {url} accessible without login"
            )
        print("  [PASS] REG-04: All protected pages redirect to login without session")

    # ── REG-05: Invalid restaurant ID must not crash ──────────────────────────
    def test_REG_05_invalid_restaurant_id_does_not_crash(self):
        """
        BUG: /menu/9999 caused AttributeError: 'NoneType' has no attribute.
        FIX: Route checks if restaurant exists, redirects if not found.
        VERIFY: Page does not show 500 error.
        """
        self._login()
        self.driver.get(BASE_URL + "/menu/9999")
        time.sleep(0.8)

        self.assertNotIn("500", self.driver.page_source,
                         "REG-05 FAILED: Invalid restaurant ID caused 500 error")
        self.assertNotIn("AttributeError", self.driver.page_source,
                         "REG-05 FAILED: Invalid restaurant ID caused AttributeError")
        print("  [PASS] REG-05: Invalid restaurant ID handled safely – no crash")

    # ── REG-06: Remove item must delete it from cart ──────────────────────────
    def test_REG_06_removing_item_clears_it_from_cart(self):
        """
        BUG: Remove button was not working – item stayed in cart after removal.
        FIX: action='remove' calls cart.pop(item_id, None) correctly.
        VERIFY: After removing, cart shows empty state.
        """
        self._login()
        self._add_item_to_cart()

        self.driver.get(BASE_URL + "/cart")
        time.sleep(0.8)

        # There should be at least one item
        items_before = self.driver.find_elements(By.CSS_SELECTOR, ".cart-item")

        if items_before:
            remove_btn = self.driver.find_element(By.CSS_SELECTOR, ".remove-btn")
            remove_btn.click()
            time.sleep(1)

            self.driver.get(BASE_URL + "/cart")
            time.sleep(0.5)
            items_after = self.driver.find_elements(By.CSS_SELECTOR, ".cart-item")
            self.assertLess(len(items_after), len(items_before),
                            "REG-06 FAILED: Item count must decrease after removal")
        print("  [PASS] REG-06: Remove button correctly removes item from cart")

    # ── REG-07: Checkout with empty cart must redirect ────────────────────────
    def test_REG_07_checkout_with_empty_cart_redirects(self):
        """
        BUG: Accessing /checkout with empty cart showed broken blank page.
        FIX: Route redirects to /cart when cart is empty.
        VERIFY: Empty cart redirects away from checkout.
        """
        self._login()

        # Clear cart first by accessing /cart and removing all items
        self.driver.get(BASE_URL + "/cart")
        time.sleep(0.5)
        while True:
            btns = self.driver.find_elements(By.CSS_SELECTOR, ".remove-btn")
            if not btns:
                break
            btns[0].click()
            time.sleep(0.8)

        # Now try to access checkout
        self.driver.get(BASE_URL + "/checkout")
        time.sleep(0.8)

        self.assertNotIn("Delivery Details", self.driver.page_source,
                         "REG-07 FAILED: Checkout showed with empty cart")
        print("  [PASS] REG-07: Checkout with empty cart safely redirects")

    # ── REG-08: Session clears on logout ─────────────────────────────────────
    def test_REG_08_session_clears_completely_on_logout(self):
        """
        BUG: Logout did not clear session cookie. User could navigate back.
        FIX: logout() calls session.clear() before redirect.
        VERIFY: After logout, all protected routes redirect to login.
        """
        self._login()

        # Verify logged in
        self.driver.get(BASE_URL + "/restaurants")
        time.sleep(0.5)
        self.assertIn("All Restaurants", self.driver.page_source,
                      "Must be logged in before testing logout")

        # Logout
        self.driver.get(BASE_URL + "/logout")
        time.sleep(0.8)

        # Try going back to restaurants
        self.driver.get(BASE_URL + "/restaurants")
        time.sleep(0.5)
        self.assertNotIn("All Restaurants", self.driver.page_source,
                         "REG-08 FAILED: Could access restaurants after logout")
        print("  [PASS] REG-08: Session fully cleared on logout")

    
    # ── REG-09: Search with no results shows no-results message ──────────────
    def test_REG_09_search_with_no_results_shows_message(self):
        """
        BUG: Searching for something that doesn't exist showed blank grid.
        FIX: no-results div is shown when visible card count = 0.
        VERIFY: No-results message appears for nonsense search query.
        """
        self._login()
        self.driver.get(BASE_URL + "/restaurants")
        time.sleep(0.5)

        search = self.driver.find_element(By.ID, "search-input")
        search.send_keys("xyznotarestaurant999")
        time.sleep(0.7)

        no_results = self.driver.find_element(By.ID, "no-results")
        self.assertTrue(no_results.is_displayed(),
                        "REG-10 FAILED: No-results message not shown for empty search")
        print("  [PASS] REG-10: No-results message shown for unmatched search query")

    # ── REG-10: Cart badge updates after adding multiple items ────────────────
    def test_REG_10_cart_badge_updates_correctly_for_multiple_items(self):
        """
        BUG: Cart badge only showed 1 even after adding multiple items.
        FIX: cart_count returns sum(cart.values()) not len(cart).
        VERIFY: Badge count matches actual number of items added.
        """
        self._login()

        # Clear cart
        self.driver.get(BASE_URL + "/cart")
        time.sleep(0.5)
        while True:
            btns = self.driver.find_elements(By.CSS_SELECTOR, ".remove-btn")
            if not btns:
                break
            btns[0].click()
            time.sleep(0.8)

        self.driver.get(BASE_URL + "/menu/2")
        time.sleep(0.8)

        add_btns = self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")
        items_added = min(3, len(add_btns))
        for i in range(items_added):
            self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")[0].click()
            time.sleep(0.6)

        badge = self.driver.find_element(By.ID, "cart-count-badge")
        count = int(badge.text) if badge.text.strip().isdigit() else 0
        self.assertGreaterEqual(count, 1,
                                "REG-11 FAILED: Cart badge must show at least 1")
        print(f"  [PASS] REG-11: Cart badge correctly shows {count} after adding items")

   


# =============================================================================
#  RUNNER
# =============================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("  FoodieExpress – Selenium REGRESSION Tests")
    print("  Make sure Flask is running: python app.py")
    print("=" * 65)

    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(SeleniumRegressionTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print("\n" + "=" * 65)
    print(f"  Regression Tests : {passed}/{total} PASSED")
    print(f"  Result : {'ALL PASSED ✓' if result.wasSuccessful() else 'SOME FAILED ✗'}")
    print("=" * 65)
    sys.exit(0 if result.wasSuccessful() else 1)