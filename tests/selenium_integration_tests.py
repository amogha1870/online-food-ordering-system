
import sys
import time
import unittest

BASE_URL = "http://127.0.0.1:5000"

# ── Selenium imports ──────────────────────────────────────────────────────────
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        NoSuchElementException, TimeoutException
    )
except ImportError:
    print("ERROR: selenium not installed.")
    print("Run:  pip install selenium webdriver-manager")
    sys.exit(1)

try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_MANAGER = True
except ImportError:
    USE_MANAGER = False


# ── Shared driver factory ─────────────────────────────────────────────────────
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


def wait_for(driver, by, value, timeout=8):
    """Wait until element is visible, then return it."""
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, value))
    )


HEADLESS = "--headless" in sys.argv




class SeleniumIntegrationTests(unittest.TestCase):
    """
    Selenium Integration Tests
    --------------------------
    Verifies that all pages and features work together end-to-end
    through a real browser session.
    """

    @classmethod
    def setUpClass(cls):
        """Create ONE browser instance shared across all tests."""
        cls.driver  = make_driver(HEADLESS)
        cls.wait    = WebDriverWait(cls.driver, 8)
        cls.base    = BASE_URL

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def _login(self, email="user@demo.com", password="demo123"):
        """Helper: navigate to login page and sign in."""
        self.driver.get(self.base + "/")
        wait_for(self.driver, By.ID, "email").clear()
        self.driver.find_element(By.ID, "email").send_keys(email)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

    def _logout(self):
        self.driver.get(self.base + "/logout")
        time.sleep(0.5)

    def _clear_cart(self):
        """Remove all items from cart via the page."""
        self.driver.get(self.base + "/cart")
        time.sleep(0.5)
        while True:
            btns = self.driver.find_elements(By.CSS_SELECTOR, ".remove-btn")
            if not btns:
                break
            btns[0].click()
            time.sleep(0.8)

    # ── INT-01: Login page renders correctly ─────────────────────────────────
   """ def test_INT_01_login_page_renders(self):
        """Login page must show FoodieExpress branding and login form."""
        self.driver.get(self.base + "/")
        time.sleep(0.5)

        page_source = self.driver.page_source
        self.assertIn("FoodieExpress", page_source,
                      "FoodieExpress branding must appear on login page")

        email_field = self.driver.find_element(By.ID, "email")
        pw_field    = self.driver.find_element(By.ID, "password")
        login_btn   = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

        self.assertTrue(email_field.is_displayed(),  "Email field must be visible")
        self.assertTrue(pw_field.is_displayed(),     "Password field must be visible")
        self.assertTrue(login_btn.is_displayed(),    "Login button must be visible")
        print("\n  [PASS] INT-01: Login page renders correctly")"""

    # ── INT-02: Invalid login shows error ─────────────────────────────────────
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
                         "Must NOT reach restaurants page with wrong credentials")
        print("  [PASS] INT-02: Invalid login shows error message")

    # ── INT-03: Valid login redirects to restaurants page ─────────────────────
    def test_INT_03_valid_login_reaches_restaurants(self):
        """Correct credentials must redirect to the restaurants page."""
        self._login()

        self.assertIn("restaurants", self.driver.current_url,
                      "URL must contain 'restaurants' after login")
        self.assertIn("All Restaurants", self.driver.page_source,
                      "Restaurants page heading must appear")
        print("  [PASS] INT-03: Valid login redirects to restaurants page")

    # ── INT-04: Restaurants page loads all 8 restaurants ─────────────────────
    def test_INT_04_restaurants_page_shows_all_restaurants(self):
        """All 8 restaurants must be visible as cards."""
        self.driver.get(self.base + "/restaurants")
        time.sleep(0.8)

        cards = self.driver.find_elements(By.CSS_SELECTOR, ".restaurant-card")
        self.assertEqual(len(cards), 8,
                         f"Expected 8 restaurant cards, found {len(cards)}")

        expected_names = ["Spice Garden", "Bella Italia", "Dragon Wok",
                          "Taco Fiesta", "Burger Barn", "Sushi Zen",
                          "Kerala Kitchen", "The Dessert Lab"]
        page = self.driver.page_source
        for name in expected_names:
            self.assertIn(name, page, f"Restaurant '{name}' not found on page")
        print("  [PASS] INT-04: All 8 restaurants displayed on restaurants page")

    # ── INT-05: Search filters restaurant cards ───────────────────────────────
    def test_INT_05_search_filters_restaurants(self):
        """Typing in the search box must filter restaurant cards."""
        self.driver.get(self.base + "/restaurants")
        time.sleep(0.5)

        search = wait_for(self.driver, By.ID, "search-input")
        search.clear()
        search.send_keys("Spice")
        time.sleep(0.6)   # wait for debounce (280ms)

        visible = [
            c for c in self.driver.find_elements(By.CSS_SELECTOR, ".restaurant-card")
            if c.is_displayed()
        ]
        self.assertGreaterEqual(len(visible), 1,
                                "At least 1 card must be visible after search")
        self.assertTrue(
            any("Spice" in c.text for c in visible),
            "Visible cards must include 'Spice Garden'"
        )
        print("  [PASS] INT-05: Search correctly filters restaurant cards")

    
    # ── INT-06: Clicking restaurant card opens correct menu ───────────────────
    def test_INT_06_clicking_card_opens_menu_page(self):
        """Clicking a restaurant card must navigate to that restaurant's menu."""
        self.driver.get(self.base + "/restaurants")
        time.sleep(0.5)

        # Click Spice Garden card (2nd highest rated = index 1 usually)
        cards = self.driver.find_elements(By.CSS_SELECTOR, ".restaurant-card")
        # Find Spice Garden specifically
        spice = None
        for card in cards:
            if "Spice Garden" in card.text:
                spice = card
                break
        self.assertIsNotNone(spice, "Spice Garden card not found")
        spice.click()
        time.sleep(1)

        self.assertIn("menu", self.driver.current_url,
                      "URL must contain 'menu' after clicking restaurant card")
        self.assertIn("Spice Garden", self.driver.page_source,
                      "Menu page must show the restaurant name")
        print("  [PASS] INT-07: Clicking restaurant card opens correct menu")

    # ── INT-07: Menu page shows items and categories ──────────────────────────
    def test_INT_07_menu_page_shows_items_and_categories(self):
        """Menu page must display food items and category filter tabs."""
        self.driver.get(self.base + "/menu/2")   # Spice Garden
        time.sleep(0.8)

        items = self.driver.find_elements(By.CSS_SELECTOR, ".menu-card")
        self.assertGreater(len(items), 0, "Menu items must be displayed")

        page = self.driver.page_source
        for category in ["Starters", "Main Course", "Breads", "Desserts", "Beverages"]:
            self.assertIn(category, page,
                          f"Category tab '{category}' must appear on menu page")
        print(f"  [PASS] INT-08: Menu shows {len(items)} items and all category tabs")

    # ── INT-08: Category tab filters menu items ───────────────────────────────
    def test_INT_08_category_tab_filters_menu_items(self):
        """Clicking a category tab must show only items of that category."""
        self.driver.get(self.base + "/menu/2")
        time.sleep(0.5)

        # Click "Starters" tab
        tabs = self.driver.find_elements(By.CSS_SELECTOR, ".cat-tab")
        starter_tab = None
        for tab in tabs:
            if "Starters" in tab.text:
                starter_tab = tab
                break
        self.assertIsNotNone(starter_tab, "Starters tab must exist")
        starter_tab.click()
        time.sleep(0.5)

        visible_items = [
            c for c in self.driver.find_elements(By.CSS_SELECTOR, ".menu-card")
            if c.is_displayed()
        ]
        self.assertGreater(len(visible_items), 0,
                           "At least one starter must be visible")
        print(f"  [PASS] INT-09: Category tab shows {len(visible_items)} starter items")

    # ── INT-09: Add to cart updates badge and shows toast ─────────────────────
    def test_INT_09_add_to_cart_updates_badge_and_shows_toast(self):
        """Adding an item must update cart badge number and show a toast."""
        self._clear_cart()
        self.driver.get(self.base + "/menu/2")
        time.sleep(0.8)

        # Get initial badge count
        badge = self.driver.find_element(By.ID, "cart-count-badge")
        before = int(badge.text) if badge.text.strip().isdigit() else 0

        # Click first Add button
        add_btns = self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")
        self.assertGreater(len(add_btns), 0, "Add buttons must exist on menu page")
        add_btns[0].click()
        time.sleep(1)

        # Badge must have increased
        after = int(self.driver.find_element(By.ID, "cart-count-badge").text)
        self.assertEqual(after, before + 1, "Cart badge must increment by 1")

        # Toast must be visible
        toast = self.driver.find_element(By.ID, "toast")
        self.assertIn("show", toast.get_attribute("class"),
                      "Toast notification must appear after adding item")
        print("  [PASS] INT-10: Cart badge updated and toast shown after adding item")

    # ── INT-10: Cart page displays added items ────────────────────────────────
    def test_INT_10_cart_page_shows_added_items(self):
        """Items added to cart must appear on the /cart page."""
        self._clear_cart()
        self.driver.get(self.base + "/menu/2")
        time.sleep(0.5)

        add_btns = self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")
        if add_btns:
            add_btns[0].click()
            time.sleep(0.6)

        self.driver.get(self.base + "/cart")
        time.sleep(0.8)

        self.assertIn("Shopping Cart", self.driver.page_source,
                      "Cart page heading must appear")
        cart_items = self.driver.find_elements(By.CSS_SELECTOR, ".cart-item")
        self.assertGreater(len(cart_items), 0,
                           "Cart must show at least 1 item")
        print(f"  [PASS] INT-11: Cart page shows {len(cart_items)} added item(s)")

    # ── INT-11: Cart quantity controls work ───────────────────────────────────
    def test_INT_11_cart_quantity_increase_decrease_works(self):
        """Plus and minus buttons on cart must change item quantity."""
        self._clear_cart()
        self.driver.get(self.base + "/menu/2")
        time.sleep(0.5)
        add_btns = self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")
        if add_btns:
            add_btns[0].click()
            time.sleep(0.6)

        self.driver.get(self.base + "/cart")
        time.sleep(0.8)

        # Get quantity before
        qty_el  = self.driver.find_element(By.CSS_SELECTOR, ".qty-num")
        qty_before = int(qty_el.text)

        # Click increase button
        increase = self.driver.find_elements(By.CSS_SELECTOR, ".qty-btn")[1]
        increase.click()
        time.sleep(1)

        self.driver.get(self.base + "/cart")
        time.sleep(0.5)
        qty_after = int(self.driver.find_element(By.CSS_SELECTOR, ".qty-num").text)
        self.assertEqual(qty_after, qty_before + 1,
                         "Quantity must increase by 1 after clicking + button")
        print(f"  [PASS] INT-12: Cart qty changed from {qty_before} to {qty_after}")

    # ── INT-12: Cart shows GST and delivery in order summary ──────────────────
    def test_INT_12_cart_shows_gst_and_delivery_fee(self):
        """Cart order summary must show GST and delivery fee."""
        self.driver.get(self.base + "/cart")
        time.sleep(0.5)

        page = self.driver.page_source
        self.assertIn("GST", page,     "GST must appear in order summary")
        self.assertIn("Order Summary", page, "Order Summary heading must appear")
        print("  [PASS] INT-13: Cart shows GST and Order Summary correctly")

    # ── INT-13: Checkout page loads with delivery form ────────────────────────
    def test_INT_13_checkout_page_loads_delivery_form(self):
        """Checkout page must show the delivery address form."""
        self._clear_cart()
        self.driver.get(self.base + "/menu/2")
        time.sleep(0.5)
        add_btns = self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")
        if add_btns:
            add_btns[0].click()
            time.sleep(0.6)

        self.driver.get(self.base + "/checkout")
        time.sleep(0.8)

        page = self.driver.page_source
        self.assertIn("Delivery Details", page,
                      "Delivery Details section must appear")

        for field_name in ["full_name", "mobile", "house", "area", "pincode"]:
            field = self.driver.find_element(By.NAME, field_name)
            self.assertTrue(field.is_displayed(),
                            f"Field '{field_name}' must be visible on checkout")
        print("  [PASS] INT-14: Checkout page shows complete delivery form")

    # ── INT-14: Payment options are displayed ─────────────────────────────────
    def test_INT_14_checkout_shows_three_payment_options(self):
        """Checkout must show UPI, Card, and COD payment options."""
        self._clear_cart()
        self.driver.get(self.base + "/menu/2")
        time.sleep(0.5)
        add_btns = self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")
        if add_btns:
            add_btns[0].click()
            time.sleep(0.6)

        self.driver.get(self.base + "/checkout")
        time.sleep(0.5)

        pay_opts = self.driver.find_elements(By.CSS_SELECTOR, ".pay-opt")
        self.assertGreaterEqual(len(pay_opts), 3,
                                "At least 3 payment options must be shown")

        page = self.driver.page_source
        self.assertIn("UPI", page,  "UPI payment option must exist")
        self.assertIn("Card", page, "Card payment option must exist")
        self.assertIn("Cash", page, "Cash on Delivery option must exist")
        print(f"  [PASS] INT-15: Checkout shows {len(pay_opts)} payment options")

    
    

    # ── INT-15: Logout redirects to login page ────────────────────────────────
    def test_INT_15_logout_redirects_to_login_page(self):
        """Clicking logout must return user to the login page."""
        self.driver.get(self.base + "/logout")
        time.sleep(0.8)

        self.assertNotIn("restaurants", self.driver.current_url,
                         "Must NOT be on restaurants page after logout")
        self.assertIn("FoodieExpress", self.driver.page_source,
                      "Login page must appear after logout")

        # Try accessing a protected page — must redirect to login
        self.driver.get(self.base + "/restaurants")
        time.sleep(0.5)
        self.assertNotIn("All Restaurants", self.driver.page_source,
                         "Must not access restaurants page after logout")
        print("  [PASS] INT-18: Logout redirects to login, blocks protected pages")



if __name__ == "__main__":
    print("=" * 65)
    print("  FoodieExpress – Selenium INTEGRATION Tests")
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
    print(f"  Result : {'ALL PASSED ✓' if result.wasSuccessful() else 'SOME FAILED ✗'}")
    print("=" * 65)
    sys.exit(0 if result.wasSuccessful() else 1)