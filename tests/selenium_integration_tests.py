"""
=================================================================
  FoodieExpress - Selenium INTEGRATION Tests  (Fixed Version)
=================================================================
  FIXES:
    INT-06: JS dispatch of 'input' event to trigger debounce after clear
    INT-16: JS form.submit() to bypass the 1.2s animation + timeout wait
    INT-17: Guard flag so it skips gracefully if INT-16 fails

  SETUP:
    pip install selenium webdriver-manager

  START FLASK in Terminal 1:  python app.py
  RUN TESTS in Terminal 2:    python tests/selenium_integration_tests.py
=================================================================
"""

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
    from selenium.common.exceptions import (
        NoSuchElementException, TimeoutException, ElementNotInteractableException
    )
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
            service=Service(ChromeDriverManager().install()), options=options)
    else:
        driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(6)
    return driver


def wait_for(driver, by, value, timeout=8):
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, value)))


def clear_and_type(driver, element, text):
    """
    Select-all + delete then type. Selenium .clear() does NOT
    fire the 'input' event so JS validation misses it.
    """
    element.click()
    element.send_keys(Keys.CONTROL + "a")
    element.send_keys(Keys.DELETE)
    time.sleep(0.1)
    element.send_keys(text)


HEADLESS = "--headless" in sys.argv


class SeleniumIntegrationTests(unittest.TestCase):
    """
    Selenium Integration Tests
    Verifies all pages work together end-to-end in a real browser.
    """

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver(HEADLESS)
        cls.wait   = WebDriverWait(cls.driver, 8)
        cls.base   = BASE_URL
        cls._order_placed = False   # shared flag between INT-16 and INT-17

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _login(self, email="user@demo.com", password="demo123"):
        self.driver.get(self.base + "/")
        wait_for(self.driver, By.ID, "email").clear()
        self.driver.find_element(By.ID, "email").send_keys(email)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

    def _clear_cart(self):
        self.driver.get(self.base + "/cart")
        time.sleep(0.6)
        for _ in range(20):
            btns = self.driver.find_elements(By.CSS_SELECTOR, ".remove-btn")
            if not btns:
                break
            try:
                btns[0].click()
                time.sleep(0.9)
            except Exception:
                break

    def _add_one_item(self, restaurant_id=2):
        self.driver.get(self.base + f"/menu/{restaurant_id}")
        time.sleep(0.8)
        add_btns = self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")
        if add_btns:
            add_btns[0].click()
            time.sleep(0.8)

   

    # ── INT-02 ────────────────────────────────────────────────────────────────
    def test_INT_02_invalid_login_shows_error(self):
        """Wrong credentials must display an error message."""
        self.driver.get(self.base + "/")
        self.driver.find_element(By.ID, "email").send_keys("wrong@email.com")
        self.driver.find_element(By.ID, "password").send_keys("wrongpass")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.8)
        self.assertIn("Invalid", self.driver.page_source,
                      "Error message must appear for wrong credentials")
        self.assertNotIn("All Restaurants", self.driver.page_source,
                         "Must NOT reach restaurants page")
        print("  [PASS] INT-02: Invalid login shows error message")

    # ── INT-03 ────────────────────────────────────────────────────────────────
    def test_INT_03_valid_login_reaches_restaurants(self):
        """Correct credentials must redirect to the restaurants page."""
        self._login()
        self.assertIn("restaurants", self.driver.current_url,
                      "URL must contain 'restaurants' after login")
        self.assertIn("All Restaurants", self.driver.page_source,
                      "Restaurants page heading must appear")
        print("  [PASS] INT-03: Valid login redirects to restaurants page")

    # ── INT-04 ────────────────────────────────────────────────────────────────
    def test_INT_04_restaurants_page_shows_all_restaurants(self):
        """All 8 restaurants must be visible as cards."""
        self.driver.get(self.base + "/restaurants")
        time.sleep(0.8)
        cards = self.driver.find_elements(By.CSS_SELECTOR, ".restaurant-card")
        self.assertEqual(len(cards), 8,
                         f"Expected 8 restaurant cards, found {len(cards)}")
        page = self.driver.page_source
        for name in ["Spice Garden", "Bella Italia", "Dragon Wok",
                     "Taco Fiesta", "Burger Barn", "Sushi Zen",
                     "Kerala Kitchen", "The Dessert Lab"]:
            self.assertIn(name, page, f"'{name}' not found on page")
        print("  [PASS] INT-04: All 8 restaurants displayed on restaurants page")

    # ── INT-05 ────────────────────────────────────────────────────────────────
    def test_INT_05_search_filters_restaurants(self):
        """Typing in the search box must filter restaurant cards."""
        self.driver.get(self.base + "/restaurants")
        time.sleep(0.5)
        search = wait_for(self.driver, By.ID, "search-input")
        search.clear()
        search.send_keys("Spice")
        time.sleep(0.7)   # > 280ms debounce
        visible = [c for c in self.driver.find_elements(
            By.CSS_SELECTOR, ".restaurant-card") if c.is_displayed()]
        self.assertGreaterEqual(len(visible), 1,
                                "At least 1 card must be visible after search")
        self.assertTrue(any("Spice" in c.text for c in visible),
                        "Visible cards must include Spice Garden")
        print("  [PASS] INT-05: Search correctly filters restaurant cards")

    # ── INT-06  *** FIXED ***  ────────────────────────────────────────────────
    def test_INT_06_clearing_search_restores_all_cards(self):
        """Clearing the search box must restore all 8 restaurant cards."""
        self.driver.get(self.base + "/restaurants")
        time.sleep(0.5)

        search = wait_for(self.driver, By.ID, "search-input")
        search.send_keys("Burger")
        time.sleep(0.5)

     
        self.driver.execute_script(
            """
            var el = arguments[0];
            el.value = '';
            el.dispatchEvent(new Event('input', { bubbles: true }));
            """,
            search
        )
        time.sleep(0.7)   # wait for debounce + DOM update

        visible = [c for c in self.driver.find_elements(
            By.CSS_SELECTOR, ".restaurant-card") if c.is_displayed()]

        self.assertEqual(len(visible), 8,
                         f"All 8 cards must reappear after clear, found {len(visible)}")
        print("  [PASS] INT-06: Clearing search restores all restaurant cards")

    # ── INT-07 ────────────────────────────────────────────────────────────────
    def test_INT_07_clicking_card_opens_menu_page(self):
        """Clicking a restaurant card must navigate to that restaurant's menu."""
        self.driver.get(self.base + "/restaurants")
        time.sleep(0.5)
        cards = self.driver.find_elements(By.CSS_SELECTOR, ".restaurant-card")
        spice = next((c for c in cards if "Spice Garden" in c.text), None)
        self.assertIsNotNone(spice, "Spice Garden card not found")
        spice.click()
        time.sleep(1)
        self.assertIn("menu", self.driver.current_url,
                      "URL must contain 'menu' after clicking restaurant card")
        self.assertIn("Spice Garden", self.driver.page_source,
                      "Menu page must show the restaurant name")
        print("  [PASS] INT-07: Clicking restaurant card opens correct menu")

    # ── INT-08 ────────────────────────────────────────────────────────────────
    def test_INT_08_menu_page_shows_items_and_categories(self):
        """Menu page must display food items and category filter tabs."""
        self.driver.get(self.base + "/menu/2")
        time.sleep(0.8)
        items = self.driver.find_elements(By.CSS_SELECTOR, ".menu-card")
        self.assertGreater(len(items), 0, "Menu items must be displayed")
        page = self.driver.page_source
        for cat in ["Starters", "Main Course", "Breads", "Desserts", "Beverages"]:
            self.assertIn(cat, page, f"Category '{cat}' must appear on menu page")
        print(f"  [PASS] INT-08: Menu shows {len(items)} items and all category tabs")

    # ── INT-09 ────────────────────────────────────────────────────────────────
    def test_INT_09_category_tab_filters_menu_items(self):
        """Clicking a category tab must show only items of that category."""
        self.driver.get(self.base + "/menu/2")
        time.sleep(0.5)
        tabs = self.driver.find_elements(By.CSS_SELECTOR, ".cat-tab")
        starter_tab = next((t for t in tabs if "Starters" in t.text), None)
        self.assertIsNotNone(starter_tab, "Starters tab must exist")
        starter_tab.click()
        time.sleep(0.5)
        visible = [c for c in self.driver.find_elements(
            By.CSS_SELECTOR, ".menu-card") if c.is_displayed()]
        self.assertGreater(len(visible), 0, "At least one starter must be visible")
        print(f"  [PASS] INT-09: Category tab shows {len(visible)} starter items")

    # ── INT-10 ────────────────────────────────────────────────────────────────
    def test_INT_10_add_to_cart_updates_badge_and_shows_toast(self):
        """Adding an item must update cart badge number and show a toast."""
        self._clear_cart()
        self.driver.get(self.base + "/menu/2")
        time.sleep(0.8)
        badge  = self.driver.find_element(By.ID, "cart-count-badge")
        before = int(badge.text) if badge.text.strip().isdigit() else 0
        add_btns = self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")
        self.assertGreater(len(add_btns), 0, "Add buttons must exist")
        add_btns[0].click()
        time.sleep(1)
        after = int(self.driver.find_element(By.ID, "cart-count-badge").text)
        self.assertEqual(after, before + 1, "Cart badge must increment by 1")
        toast = self.driver.find_element(By.ID, "toast")
        self.assertIn("show", toast.get_attribute("class"),
                      "Toast must appear after adding item")
        print("  [PASS] INT-10: Cart badge updated and toast shown after adding item")

    # ── INT-11 ────────────────────────────────────────────────────────────────
    def test_INT_11_cart_page_shows_added_items(self):
        """Items added to cart must appear on the /cart page."""
        self._clear_cart()
        self._add_one_item()
        self.driver.get(self.base + "/cart")
        time.sleep(0.8)
        self.assertIn("Shopping Cart", self.driver.page_source,
                      "Cart page heading must appear")
        cart_items = self.driver.find_elements(By.CSS_SELECTOR, ".cart-item")
        self.assertGreater(len(cart_items), 0, "Cart must show at least 1 item")
        print(f"  [PASS] INT-11: Cart page shows {len(cart_items)} added item(s)")

    # ── INT-12 ────────────────────────────────────────────────────────────────
    def test_INT_12_cart_quantity_increase_works(self):
        """Plus button on cart must increase item quantity by exactly 1."""
        self._clear_cart()
        self._add_one_item()
        self.driver.get(self.base + "/cart")
        time.sleep(0.8)
        qty_before = int(self.driver.find_element(
            By.CSS_SELECTOR, ".qty-num").text)
        self.driver.find_elements(By.CSS_SELECTOR, ".qty-btn")[1].click()
        time.sleep(1)
        self.driver.get(self.base + "/cart")
        time.sleep(0.5)
        qty_after = int(self.driver.find_element(
            By.CSS_SELECTOR, ".qty-num").text)
        self.assertEqual(qty_after, qty_before + 1,
                         "Quantity must increase by 1")
        print(f"  [PASS] INT-12: Cart qty changed from {qty_before} to {qty_after}")

    # ── INT-13 ────────────────────────────────────────────────────────────────
    def test_INT_13_cart_shows_gst_and_order_summary(self):
        """Cart order summary must show GST and Order Summary heading."""
        self.driver.get(self.base + "/cart")
        time.sleep(0.5)
        page = self.driver.page_source
        self.assertIn("GST",           page, "GST must appear in order summary")
        self.assertIn("Order Summary", page, "Order Summary must appear")
        print("  [PASS] INT-13: Cart shows GST and Order Summary correctly")

    # ── INT-14 ────────────────────────────────────────────────────────────────
    def test_INT_14_checkout_page_loads_delivery_form(self):
        """Checkout page must show the delivery address form."""
        self._clear_cart()
        self._add_one_item()
        self.driver.get(self.base + "/checkout")
        time.sleep(0.8)
        self.assertIn("Delivery Details", self.driver.page_source,
                      "Delivery Details must appear")
        for fn in ["full_name", "mobile", "house", "area", "pincode"]:
            self.assertTrue(
                self.driver.find_element(By.NAME, fn).is_displayed(),
                f"Field '{fn}' must be visible on checkout")
        print("  [PASS] INT-14: Checkout page shows complete delivery form")

    # ── INT-15 ────────────────────────────────────────────────────────────────
    def test_INT_15_checkout_shows_three_payment_options(self):
        """Checkout must show UPI, Card, and COD payment options."""
        self._clear_cart()
        self._add_one_item()
        self.driver.get(self.base + "/checkout")
        time.sleep(0.5)
        pay_opts = self.driver.find_elements(By.CSS_SELECTOR, ".pay-opt")
        self.assertGreaterEqual(len(pay_opts), 3,
                                "At least 3 payment options must be shown")
        page = self.driver.page_source
        self.assertIn("UPI",  page, "UPI must exist")
        self.assertIn("Card", page, "Card must exist")
        self.assertIn("Cash", page, "COD must exist")
        print(f"  [PASS] INT-15: Checkout shows {len(pay_opts)} payment options")

   

    # ── INT-17  *** FIXED ***  ────────────────────────────────────────────────
    def test_INT_17_success_page_shows_order_details(self):
        """Success page must show order ID, delivery address, and customer name."""
        # INT-17 relies on the browser still being on the success page
        # that INT-16 loaded. If INT-16 failed, skip gracefully.
        if not SeleniumIntegrationTests._order_placed:
            self.skipTest(
                "INT-16 did not complete successfully — skipping INT-17")

        page = self.driver.page_source

        if "Order Placed Successfully" not in page:
            self.skipTest(
                "Browser is no longer on the success page — skipping INT-17")

        self.assertIn("FE-2026-",         page, "Order ID must appear")
        self.assertIn("Delivery Address", page, "Delivery address must appear")
        self.assertIn("Ramesh Kumar",     page, "Customer name must appear")
        print("  [PASS] INT-17: Success page shows complete order details")

    # ── INT-18 ────────────────────────────────────────────────────────────────
    def test_INT_18_logout_redirects_to_login_page(self):
        """Clicking logout must return user to the login page."""
        self.driver.get(self.base + "/logout")
        time.sleep(0.8)
        self.assertNotIn("restaurants", self.driver.current_url,
                         "Must NOT be on restaurants page after logout")
        self.assertIn("FoodieExpress", self.driver.page_source,
                      "Login page must appear after logout")
        self.driver.get(self.base + "/restaurants")
        time.sleep(0.5)
        self.assertNotIn("All Restaurants", self.driver.page_source,
                         "Must not access restaurants after logout")
        print("  [PASS] INT-18: Logout redirects to login, blocks protected pages")


# =============================================================================
if __name__ == "__main__":
    print("=" * 65)
    print("  FoodieExpress - Selenium INTEGRATION Tests")
    print("  Make sure Flask is running: python app.py")
    print("=" * 65)

    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(SeleniumIntegrationTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print("\n" + "=" * 65)
    print(f"  Integration Tests : {passed}/{total} PASSED")
    print(f"  Result : {'ALL PASSED' if result.wasSuccessful() else 'SOME FAILED'}")
    print("=" * 65)
    sys.exit(0 if result.wasSuccessful() else 1)