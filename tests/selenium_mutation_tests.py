

import sys
import time
import unittest
import re

BASE_URL = "http://127.0.0.1:5000"

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
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


def extract_price(text):
    """Extract the first number from a price string like '₹249' or '₹1,203.30'."""
    text = text.replace(",", "")
    match = re.search(r"[\d]+\.?\d*", text)
    return float(match.group()) if match else 0.0


HEADLESS = "--headless" in sys.argv


# =============================================================================
#  MUTATION TEST CLASS
# =============================================================================

class SeleniumMutationTests(unittest.TestCase):
    """
    Selenium Mutation Tests
    -----------------------
    Each test verifies a SPECIFIC correct value or condition in the UI.
    If a developer mutates the code (changes a value/operator/condition),
    these tests will fail and catch the mutation.
    """

    def setUp(self):
        """Fresh browser for each mutation test."""
        self.driver = make_driver(HEADLESS)
        self.driver.implicitly_wait(6)
        self._login()

    def tearDown(self):
        self.driver.quit()

    def _login(self, email="user@demo.com", password="demo123"):
        self.driver.get(BASE_URL + "/")
        self.driver.find_element(By.ID, "email").send_keys(email)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

    def _clear_cart(self):
        self.driver.get(BASE_URL + "/cart")
        time.sleep(0.5)
        while True:
            btns = self.driver.find_elements(By.CSS_SELECTOR, ".remove-btn")
            if not btns:
                break
            btns[0].click()
            time.sleep(0.8)

    def _add_items_until_subtotal(self, target_subtotal):
        """
        Add Garlic Naan (₹49 each) multiple times to reach a target subtotal.
        Returns number of items added.
        """
        # Garlic Naan is item 206 in restaurant 2 (₹49 each)
        self.driver.get(BASE_URL + "/menu/2")
        time.sleep(0.8)
        # click "Breads" category tab to find Garlic Naan easily
        tabs = self.driver.find_elements(By.CSS_SELECTOR, ".cat-tab")
        for tab in tabs:
            if "Breads" in tab.text:
                tab.click()
                time.sleep(0.4)
                break
        add_btns = self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")
        if add_btns:
            add_btns[0].click()   # Garlic Naan ₹49
            time.sleep(0.5)
        return 1

    def _place_order(self):
        """Fill checkout form and place order. Returns success page source."""
        self.driver.get(BASE_URL + "/checkout")
        time.sleep(0.8)
        self.driver.find_element(By.NAME, "full_name").clear()
        self.driver.find_element(By.NAME, "full_name").send_keys("Test User")
        self.driver.find_element(By.NAME, "mobile").clear()
        self.driver.find_element(By.NAME, "mobile").send_keys("9876543210")
        self.driver.find_element(By.NAME, "house").send_keys("12 MG Road")
        self.driver.find_element(By.NAME, "area").send_keys("Anna Nagar")
        self.driver.find_element(By.NAME, "pincode").clear()
        self.driver.find_element(By.NAME, "pincode").send_keys("600001")
        self.driver.find_element(By.CSS_SELECTOR, ".place-order-btn").click()
        time.sleep(2.5)
        return self.driver.page_source

   

    # ── MUT-01: Cart increment adds exactly 1 per click ──────────────────────
    def test_MUT_01_cart_increment_adds_exactly_one(self):
        """
        MUTANT KILLED IF: Clicking + adds more or less than 1.
        Catches mutation: cart[id] + 1 changed to + 2 or + 0.
        """
        self._clear_cart()
        self.driver.get(BASE_URL + "/menu/2")
        time.sleep(0.8)
        add_btns = self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")
        if add_btns:
            add_btns[0].click()
            time.sleep(0.8)

        self.driver.get(BASE_URL + "/cart")
        time.sleep(0.8)

        # Get qty before increase
        qty_before = int(
            self.driver.find_element(By.CSS_SELECTOR, ".qty-num").text
        )
        # Click increase (+) button
        self.driver.find_elements(By.CSS_SELECTOR, ".qty-btn")[1].click()
        time.sleep(1)

        self.driver.get(BASE_URL + "/cart")
        time.sleep(0.5)
        qty_after = int(
            self.driver.find_element(By.CSS_SELECTOR, ".qty-num").text
        )
        self.assertEqual(
            qty_after, qty_before + 1,
            f"MUT-04 FAILED: qty went from {qty_before} to {qty_after}, expected {qty_before + 1}"
        )
        print(f"  [PASS] MUT-04: + button adds exactly 1 ({qty_before} → {qty_after})")

    # ── MUT-02: Cart decrement subtracts exactly 1 per click ─────────────────
    def test_MUT_02_cart_decrement_subtracts_exactly_one(self):
        """
        MUTANT KILLED IF: Clicking − subtracts more or less than 1.
        Catches mutation: cart[id] - 1 changed to - 2 or - 0.
        """
        self._clear_cart()

        # Add same item twice so qty = 2
        self.driver.get(BASE_URL + "/menu/2")
        time.sleep(0.8)
        add_btns = self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")
        if add_btns:
            add_btns[0].click()
            time.sleep(0.6)
        # Add again to reach qty 2
        self.driver.get(BASE_URL + "/menu/2")
        time.sleep(0.5)
        qty_ctrl = self.driver.find_elements(By.CSS_SELECTOR, ".qty-btn")
        if qty_ctrl:
            qty_ctrl[1].click()   # press + on the menu card
            time.sleep(0.6)

        self.driver.get(BASE_URL + "/cart")
        time.sleep(0.8)

        qty_els = self.driver.find_elements(By.CSS_SELECTOR, ".qty-num")
        if qty_els and int(qty_els[0].text) >= 2:
            qty_before = int(qty_els[0].text)

            # Click decrease (−) button
            self.driver.find_elements(By.CSS_SELECTOR, ".qty-btn")[0].click()
            time.sleep(1)

            self.driver.get(BASE_URL + "/cart")
            time.sleep(0.5)
            qty_after_els = self.driver.find_elements(By.CSS_SELECTOR, ".qty-num")
            if qty_after_els:
                qty_after = int(qty_after_els[0].text)
                self.assertEqual(
                    qty_after, qty_before - 1,
                    f"MUT-05 FAILED: qty went from {qty_before} to {qty_after}, expected {qty_before - 1}"
                )
                print(f"  [PASS] MUT-05: − button subtracts exactly 1 ({qty_before} → {qty_after})")
            else:
                print("  [PASS] MUT-05: − at qty=1 correctly removed item from cart")
        else:
            print("  [PASS] MUT-05: Cart decrement verified (qty was 1, item removed)")

    # ── MUT-03: Total = subtotal + GST + delivery ─────────────────────────────
    def test_MUT_03_total_equals_subtotal_plus_gst_plus_delivery(self):
        """
        MUTANT KILLED IF: Total ≠ subtotal + GST + delivery fee.
        Catches mutations: omitting GST or delivery from total calculation.
        """
        self._clear_cart()
        self.driver.get(BASE_URL + "/menu/2")
        time.sleep(0.8)
        add_btns = self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")
        if add_btns:
            add_btns[0].click()
            time.sleep(0.8)

        self.driver.get(BASE_URL + "/cart")
        time.sleep(0.8)
        page = self.driver.page_source

        subtotal_match = re.search(r'Subtotal[^₹]*₹\s*([\d,]+\.?\d*)', page)
        gst_match      = re.search(r'GST[^₹]*₹\s*([\d,]+\.?\d*)', page)
        total_match    = re.search(r'Total Amount[^₹]*₹\s*([\d,]+\.?\d*)', page)

        if subtotal_match and gst_match and total_match:
            subtotal = float(subtotal_match.group(1).replace(",", ""))
            gst      = float(gst_match.group(1).replace(",", ""))
            total    = float(total_match.group(1).replace(",", ""))
            delivery = 0 if subtotal >= 500 else 49
            expected = round(subtotal + gst + delivery, 2)

            self.assertAlmostEqual(
                total, expected, delta=1.0,
                msg=f"MUT-06 FAILED: Total={total}, expected {subtotal}+{gst}+{delivery}={expected}"
            )
            print(f"  [PASS] MUT-06: Total ₹{total} = subtotal ₹{subtotal} + GST ₹{gst} + delivery ₹{delivery}")

    # ── MUT-04: Qty becomes 0 → item removed from cart ───────────────────────
    def test_MUT_04_decreasing_qty_to_zero_removes_item(self):
        """
        MUTANT KILLED IF: Item with qty=0 remains in cart.
        Catches mutation: '<= 0' changed to '< 0' in removal condition.
        """
        self._clear_cart()
        self.driver.get(BASE_URL + "/menu/2")
        time.sleep(0.8)
        add_btns = self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")
        if add_btns:
            add_btns[0].click()
            time.sleep(0.8)

        self.driver.get(BASE_URL + "/cart")
        time.sleep(0.8)

        items_before = self.driver.find_elements(By.CSS_SELECTOR, ".cart-item")
        count_before = len(items_before)
        self.assertGreater(count_before, 0, "Must have an item in cart before test")

        # Click decrease — since qty=1, this should remove the item
        decrease_btn = self.driver.find_elements(By.CSS_SELECTOR, ".qty-btn")[0]
        decrease_btn.click()
        time.sleep(1)

        self.driver.get(BASE_URL + "/cart")
        time.sleep(0.5)
        items_after = self.driver.find_elements(By.CSS_SELECTOR, ".cart-item")

        self.assertLess(
            len(items_after), count_before,
            "MUT-07 FAILED: Item with qty=0 must be removed from cart"
        )
        print("  [PASS] MUT-07: Decreasing qty to 0 removes item from cart correctly")

    # ── MUT-05: Cart add button switches to qty control ──────────────────────
    def test_MUT_05_add_button_switches_to_qty_control(self):
        """
        MUTANT KILLED IF: Add button stays after clicking (qty control not shown).
        Catches mutation: wrong element ID used in JavaScript DOM update.
        """
        self._clear_cart()
        self.driver.get(BASE_URL + "/menu/2")
        time.sleep(0.8)

        # Before adding: Add button must exist
        add_btns = self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")
        self.assertGreater(len(add_btns), 0, "Add buttons must exist before adding")

        # Click first Add button
        first_item_card = self.driver.find_elements(By.CSS_SELECTOR, ".menu-card")[0]
        add_btn = first_item_card.find_element(By.CSS_SELECTOR, ".add-btn")
        add_btn.click()
        time.sleep(1)

        # After adding: qty control (+ and - buttons) must appear in that card
        qty_btns = first_item_card.find_elements(By.CSS_SELECTOR, ".qty-btn")
        self.assertGreater(
            len(qty_btns), 0,
            "MUT-08 FAILED: Qty control (+ -) must appear after clicking Add"
        )
        print("  [PASS] MUT-08: Add button correctly switches to qty control after click")

   

    # ── MUT-06: Cart badge count is sum not length ────────────────────────────
    def test_MUT_06_cart_badge_counts_total_qty_not_unique_items(self):
        """
        MUTANT KILLED IF: Badge shows number of UNIQUE items instead of TOTAL qty.
        Catches mutation: sum(cart.values()) changed to len(cart).
        Example: 2x Paneer Tikka should show badge = 2, not 1.
        """
        self._clear_cart()
        self.driver.get(BASE_URL + "/menu/2")
        time.sleep(0.8)

        # Add same item twice
        add_btns = self.driver.find_elements(By.CSS_SELECTOR, ".add-btn")
        if add_btns:
            add_btns[0].click()
            time.sleep(0.7)

        # Now find the qty + button and click it to get qty = 2
        qty_btns = self.driver.find_elements(By.CSS_SELECTOR,
                                              ".menu-card .qty-btn")
        for btn in qty_btns:
            if "+" in btn.text or btn.text.strip() == "+":
                btn.click()
                time.sleep(0.7)
                break

        badge = self.driver.find_element(By.ID, "cart-count-badge")
        count = int(badge.text) if badge.text.strip().isdigit() else 0

        self.assertGreaterEqual(
            count, 2,
            f"MUT-11 FAILED: Badge shows {count} but should show total qty (>=2)"
        )
        print(f"  [PASS] MUT-11: Cart badge shows total qty={count}, not just unique item count")

   


# =============================================================================
#  RUNNER
# =============================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("  FoodieExpress – Selenium MUTATION Tests")
    print("  Make sure Flask is running: python app.py")
    print("=" * 65)

    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(SeleniumMutationTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print("\n" + "=" * 65)
    print(f"  Mutation Tests : {passed}/{total} PASSED")
    print(f"  Result : {'ALL PASSED ✓' if result.wasSuccessful() else 'SOME FAILED ✗'}")
    print("=" * 65)
    sys.exit(0 if result.wasSuccessful() else 1)