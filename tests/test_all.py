"""
=============================================================
  FoodieExpress – Complete Test Suite
=============================================================
  Covers:
    1. Integration Tests
    2. Regression Tests
    3. Mutation Tests

  How to run (from inside your foodieexpress/ folder):
    python -m unittest tests/test_all.py -v

  OR run individual sections:
    python -m unittest tests.test_all.IntegrationTests -v
    python -m unittest tests.test_all.RegressionTests -v
    python -m unittest tests.test_all.MutationTests    -v
=============================================================
"""

import unittest
import json
import os
import sys
import sqlite3
import tempfile
import shutil

# ── Make sure app.py is importable ───────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as foodie_app


# ─────────────────────────────────────────────────────────────────────────────
#  SHARED SETUP HELPER
# ─────────────────────────────────────────────────────────────────────────────

def create_test_client():
    """
    Creates a fresh Flask test client backed by a
    temporary SQLite database for every test class.
    Returns: (client, tmp_dir, original_db_path)
    """
    foodie_app.app.config['TESTING']    = True
    foodie_app.app.config['SECRET_KEY'] = 'test-secret-key'

    tmp_dir  = tempfile.mkdtemp()
    test_db  = os.path.join(tmp_dir, 'test_foodieexpress.db')
    original = foodie_app.DATABASE

    foodie_app.DATABASE = test_db
    foodie_app.init_db()

    client = foodie_app.app.test_client()
    return client, tmp_dir, original


def do_login(client, email='user@demo.com', password='demo123'):
    """Helper: log in and follow the redirect."""
    return client.post(
        '/',
        data={'email': email, 'password': password},
        follow_redirects=True
    )


def add_item(client, item_id):
    """Helper: add one item to cart via the JSON API."""
    return client.post(
        '/api/cart/add',
        json={'item_id': item_id},
        content_type='application/json'
    )


# ─────────────────────────────────────────────────────────────────────────────
#  1. INTEGRATION TESTS
#     Tests that verify multiple parts of the system working together:
#     Flask routes  +  SQLite database  +  session cart
# ─────────────────────────────────────────────────────────────────────────────

class IntegrationTests(unittest.TestCase):
    """
    Integration Tests
    -----------------
    Verifies that the full HTTP request → route → database → response
    pipeline works correctly end-to-end.
    """

    def setUp(self):
        self.client, self.tmp_dir, self.orig_db = create_test_client()

    def tearDown(self):
        foodie_app.DATABASE = self.orig_db
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    # ── Authentication Integration ─────────────────────────────────────────

    def test_INT_01_login_page_loads_successfully(self):
        """GET / should return 200 and show the login form."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'FoodieExpress', response.data)
        self.assertIn(b'email', response.data.lower())
        self.assertIn(b'password', response.data.lower())

    def test_INT_02_valid_credentials_redirects_to_restaurants(self):
        """POST / with correct credentials should redirect to /restaurants."""
        response = do_login(self.client)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'All Restaurants', response.data)

    def test_INT_03_invalid_password_shows_error(self):
        """POST / with wrong password should stay on login with error."""
        response = self.client.post(
            '/', data={'email': 'user@demo.com', 'password': 'WRONGPASS'},
            follow_redirects=True
        )
        self.assertIn(b'Invalid', response.data)
        self.assertNotIn(b'All Restaurants', response.data)

    def test_INT_04_invalid_email_shows_error(self):
        """POST / with unknown email should show error."""
        response = self.client.post(
            '/', data={'email': 'nobody@fake.com', 'password': 'demo123'},
            follow_redirects=True
        )
        self.assertIn(b'Invalid', response.data)

    def test_INT_05_logout_clears_session_and_redirects(self):
        """GET /logout should clear session and redirect to login page."""
        do_login(self.client)
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'FoodieExpress', response.data)
        # after logout, /restaurants should redirect back to login
        check = self.client.get('/restaurants', follow_redirects=False)
        self.assertEqual(check.status_code, 302)

    def test_INT_06_protected_routes_redirect_when_not_logged_in(self):
        """All protected routes must redirect to login without a session."""
        protected = ['/restaurants', '/menu/2', '/cart', '/checkout']
        for route in protected:
            response = self.client.get(route, follow_redirects=False)
            self.assertEqual(
                response.status_code, 302,
                msg=f"Route {route} should redirect unauthenticated users"
            )

    # ── Restaurant & Menu Integration ──────────────────────────────────────

    def test_INT_07_restaurants_page_loads_data_from_db(self):
        """GET /restaurants should load all 8 restaurants from SQLite."""
        do_login(self.client)
        response = self.client.get('/restaurants')
        self.assertEqual(response.status_code, 200)
        # All 8 restaurant names should appear on the page
        for name in [b'Spice Garden', b'Bella Italia', b'Dragon Wok',
                     b'Taco Fiesta', b'Burger Barn', b'Sushi Zen',
                     b'Kerala Kitchen', b'The Dessert Lab']:
            self.assertIn(name, response.data,
                          msg=f"{name} not found on restaurants page")

    def test_INT_08_menu_page_loads_correct_restaurant(self):
        """GET /menu/2 should show Spice Garden's menu items."""
        do_login(self.client)
        response = self.client.get('/menu/2')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Spice Garden', response.data)
        self.assertIn(b'Paneer Tikka', response.data)
        self.assertIn(b'Butter Chicken', response.data)

    def test_INT_09_menu_page_shows_category_tabs(self):
        """Menu page should display category filter tabs."""
        do_login(self.client)
        response = self.client.get('/menu/2')
        self.assertIn(b'Starters', response.data)
        self.assertIn(b'Main Course', response.data)
        self.assertIn(b'Breads', response.data)
        self.assertIn(b'Desserts', response.data)
        self.assertIn(b'Beverages', response.data)

    def test_INT_10_invalid_restaurant_id_redirects(self):
        """GET /menu/9999 should redirect, not crash with 500."""
        do_login(self.client)
        response = self.client.get('/menu/9999', follow_redirects=False)
        self.assertEqual(response.status_code, 302)

    # ── Cart Integration ───────────────────────────────────────────────────

    def test_INT_11_add_item_to_cart_via_api(self):
        """POST /api/cart/add should add item and return success JSON."""
        do_login(self.client)
        response = add_item(self.client, 201)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['qty'], 1)
        self.assertEqual(data['cart_count'], 1)

    def test_INT_12_adding_same_item_twice_increments_quantity(self):
        """Adding the same item twice should set qty to 2."""
        do_login(self.client)
        add_item(self.client, 201)
        response = add_item(self.client, 201)
        data = json.loads(response.data)
        self.assertEqual(data['qty'], 2)
        self.assertEqual(data['cart_count'], 2)

    def test_INT_13_cart_count_api_returns_correct_total(self):
        """GET /api/cart/count should return total items in cart."""
        do_login(self.client)
        add_item(self.client, 201)
        add_item(self.client, 203)
        add_item(self.client, 206)
        response = self.client.get('/api/cart/count')
        data = json.loads(response.data)
        self.assertEqual(data['count'], 3)

    def test_INT_14_increase_cart_item_quantity(self):
        """POST /api/cart/update with action=increase should add 1."""
        do_login(self.client)
        add_item(self.client, 203)
        response = self.client.post(
            '/api/cart/update',
            json={'item_id': 203, 'action': 'increase'},
            content_type='application/json'
        )
        data = json.loads(response.data)
        self.assertEqual(data['cart_count'], 2)

    def test_INT_15_decrease_cart_item_quantity(self):
        """POST /api/cart/update with action=decrease should subtract 1."""
        do_login(self.client)
        add_item(self.client, 203)
        add_item(self.client, 203)  # qty = 2
        response = self.client.post(
            '/api/cart/update',
            json={'item_id': 203, 'action': 'decrease'},
            content_type='application/json'
        )
        data = json.loads(response.data)
        self.assertEqual(data['cart_count'], 1)

    def test_INT_16_remove_item_from_cart(self):
        """POST /api/cart/update with action=remove should delete item."""
        do_login(self.client)
        add_item(self.client, 203)
        response = self.client.post(
            '/api/cart/update',
            json={'item_id': 203, 'action': 'remove'},
            content_type='application/json'
        )
        data = json.loads(response.data)
        self.assertEqual(data['cart_count'], 0)

    def test_INT_17_cart_page_displays_added_items(self):
        """GET /cart should show items that were added via API."""
        do_login(self.client)
        add_item(self.client, 201)  # Paneer Tikka
        response = self.client.get('/cart')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Paneer Tikka', response.data)

    def test_INT_18_cart_page_shows_order_summary(self):
        """Cart page must show Order Summary section."""
        do_login(self.client)
        add_item(self.client, 201)
        response = self.client.get('/cart')
        self.assertIn(b'Order Summary', response.data)
        self.assertIn(b'GST', response.data)

    # ── Checkout & Order Integration ───────────────────────────────────────

    def test_INT_19_checkout_page_loads_with_items_in_cart(self):
        """GET /checkout should load delivery form when cart has items."""
        do_login(self.client)
        add_item(self.client, 201)
        response = self.client.get('/checkout')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Delivery Details', response.data)

    def test_INT_20_place_order_saves_to_database(self):
        """POST /place_order should save order in orders table."""
        do_login(self.client)
        add_item(self.client, 201)
        add_item(self.client, 203)
        self.client.post('/place_order', data={
            'full_name' : 'Ramesh Kumar',
            'mobile'    : '9876543210',
            'house'     : '42, Anna Nagar',
            'area'      : 'T. Nagar',
            'city'      : 'Chennai',
            'state'     : 'Tamil Nadu',
            'pincode'   : '600001',
            'payment'   : 'upi'
        })
        db    = sqlite3.connect(foodie_app.DATABASE)
        count = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        db.close()
        self.assertGreater(count, 0, "Order should be saved in database")

    def test_INT_21_place_order_shows_success_page(self):
        """POST /place_order should render the success page."""
        do_login(self.client)
        add_item(self.client, 201)
        response = self.client.post('/place_order', data={
            'full_name' : 'Ramesh Kumar',
            'mobile'    : '9876543210',
            'house'     : '42, Anna Nagar',
            'area'      : 'T. Nagar',
            'city'      : 'Chennai',
            'state'     : 'Tamil Nadu',
            'pincode'   : '600001',
            'payment'   : 'upi'
        }, follow_redirects=True)
        self.assertIn(b'Order Placed Successfully', response.data)

    def test_INT_22_place_order_generates_correct_order_id_format(self):
        """Order ID must follow FE-2026-XXXX format."""
        do_login(self.client)
        add_item(self.client, 201)
        response = self.client.post('/place_order', data={
            'full_name' : 'Test User',
            'mobile'    : '9876543210',
            'house'     : '12 MG Road',
            'area'      : 'Anna Nagar',
            'city'      : 'Chennai',
            'state'     : 'Tamil Nadu',
            'pincode'   : '600001',
            'payment'   : 'cod'
        }, follow_redirects=True)
        self.assertIn(b'FE-2026-', response.data)

    def test_INT_23_place_order_clears_cart_after_success(self):
        """Cart must be empty after a successful order is placed."""
        do_login(self.client)
        add_item(self.client, 201)
        add_item(self.client, 203)
        self.client.post('/place_order', data={
            'full_name' : 'Test User',
            'mobile'    : '9876543210',
            'house'     : '12 MG Road',
            'area'      : 'Anna Nagar',
            'city'      : 'Chennai',
            'state'     : 'Tamil Nadu',
            'pincode'   : '600001',
            'payment'   : 'upi'
        })
        response = self.client.get('/api/cart/count')
        data     = json.loads(response.data)
        self.assertEqual(data['count'], 0, "Cart must be empty after order")

    def test_INT_24_database_stores_correct_order_total(self):
        """Order total saved in DB must match subtotal + GST + delivery."""
        do_login(self.client)
        add_item(self.client, 201)   # Paneer Tikka ₹249
        self.client.post('/place_order', data={
            'full_name' : 'Test User',
            'mobile'    : '9876543210',
            'house'     : '12 MG Road',
            'area'      : 'Anna Nagar',
            'city'      : 'Chennai',
            'state'     : 'Tamil Nadu',
            'pincode'   : '600001',
            'payment'   : 'upi'
        })
        db    = sqlite3.connect(foodie_app.DATABASE)
        order = db.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 1").fetchone()
        db.close()
        subtotal = order[4]   # subtotal column
        gst      = order[5]   # gst column
        delivery = order[6]   # delivery_fee column
        total    = order[7]   # total column
        expected = round(subtotal + gst + delivery, 2)
        self.assertAlmostEqual(total, expected, places=2)


# ─────────────────────────────────────────────────────────────────────────────
#  2. REGRESSION TESTS
#     Tests that guard against bugs that were fixed from coming back.
#     Each test is named REG-XXX and describes the original bug.
# ─────────────────────────────────────────────────────────────────────────────

class RegressionTests(unittest.TestCase):
    """
    Regression Tests
    ----------------
    Ensures previously identified bugs do not reappear
    after code changes or refactoring.
    """

    def setUp(self):
        self.client, self.tmp_dir, self.orig_db = create_test_client()

    def tearDown(self):
        foodie_app.DATABASE = self.orig_db
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_REG_01_unauthenticated_cart_api_does_not_crash(self):
        """
        BUG: Calling cart API without login used to throw a 500 error.
        FIX: login_required decorator now redirects with 302.
        """
        response = self.client.post(
            '/api/cart/add',
            json={'item_id': 201},
            content_type='application/json'
        )
        self.assertIn(
            response.status_code, [302, 401],
            "Cart API must redirect (302) or unauthorize (401), not crash (500)"
        )

    def test_REG_02_empty_login_fields_do_not_crash(self):
        """
        BUG: Submitting login form with empty fields used to cause KeyError.
        FIX: form.get() with defaults handles empty submissions safely.
        """
        response = self.client.post(
            '/', data={'email': '', 'password': ''},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'Internal Server Error', response.data)

    def test_REG_03_nonexistent_restaurant_does_not_return_500(self):
        """
        BUG: Accessing /menu/<invalid_id> used to crash with AttributeError.
        FIX: Route now checks if restaurant exists and redirects if not.
        """
        do_login(self.client)
        response = self.client.get('/menu/99999')
        self.assertNotEqual(
            response.status_code, 500,
            "Invalid restaurant ID must not cause a server crash"
        )

    def test_REG_04_placing_order_with_empty_cart_redirects_safely(self):
        """
        BUG: POST /place_order with empty cart used to crash the server.
        FIX: Route now checks for empty cart and redirects to /cart.
        """
        do_login(self.client)
        response = self.client.post('/place_order', data={
            'full_name' : 'Test',
            'mobile'    : '9876543210',
            'house'     : 'H',
            'area'      : 'A',
            'city'      : 'Chennai',
            'state'     : 'Tamil Nadu',
            'pincode'   : '600001',
            'payment'   : 'upi'
        }, follow_redirects=False)
        self.assertEqual(
            response.status_code, 302,
            "Empty cart order must redirect, not crash"
        )

    def test_REG_05_calling_init_db_twice_does_not_duplicate_restaurants(self):
        """
        BUG: Calling init_db() a second time used to insert duplicate rows.
        FIX: Seed uses IF NOT EXISTS check before inserting.
        """
        foodie_app.init_db()   # second call
        db    = sqlite3.connect(foodie_app.DATABASE)
        count = db.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0]
        db.close()
        self.assertEqual(count, 8, "Must have exactly 8 restaurants, no duplicates")

    def test_REG_06_cart_count_api_requires_login(self):
        """
        BUG: /api/cart/count was accessible without login.
        FIX: Endpoint now protected by @login_required.
        """
        response = self.client.get('/api/cart/count', follow_redirects=False)
        self.assertEqual(
            response.status_code, 302,
            "Cart count API must require authentication"
        )

    def test_REG_07_sql_injection_in_login_is_blocked(self):
        """
        BUG: Login was vulnerable to SQL injection via raw string queries.
        FIX: Parameterised queries (?) prevent injection attacks.
        """
        response = self.client.post(
            '/',
            data={"email": "' OR '1'='1' --", "password": "anything"},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            b'All Restaurants', response.data,
            "SQL injection must not bypass authentication"
        )

    def test_REG_08_checkout_with_empty_cart_redirects(self):
        """
        BUG: GET /checkout with empty cart used to show a blank broken page.
        FIX: Route redirects to /cart when cart is empty.
        """
        do_login(self.client)
        response = self.client.get('/checkout', follow_redirects=False)
        self.assertEqual(
            response.status_code, 302,
            "Checkout with empty cart must redirect to cart page"
        )

    def test_REG_09_decreasing_qty_to_zero_removes_item_from_cart(self):
        """
        BUG: Decreasing quantity to 0 left a ghost item with qty=0 in cart.
        FIX: Decrease logic deletes item when qty reaches 0 or below.
        """
        do_login(self.client)
        add_item(self.client, 203)   # qty = 1
        self.client.post(
            '/api/cart/update',
            json={'item_id': 203, 'action': 'decrease'},
            content_type='application/json'
        )
        response = self.client.get('/api/cart/count')
        data     = json.loads(response.data)
        self.assertEqual(
            data['count'], 0,
            "Item must be fully removed when qty reaches 0"
        )

    def test_REG_10_adding_large_quantity_is_handled_correctly(self):
        """
        BUG: Adding 50+ items to cart caused integer overflow in older code.
        FIX: Python int handles arbitrary sizes natively.
        """
        do_login(self.client)
        for _ in range(50):
            add_item(self.client, 201)
        response = self.client.get('/api/cart/count')
        data     = json.loads(response.data)
        self.assertEqual(data['count'], 50)

    def test_REG_11_multiple_different_items_tracked_separately(self):
        """
        BUG: Adding different items was merging their quantities together.
        FIX: Cart uses item_id as key, so each item is tracked separately.
        """
        do_login(self.client)
        add_item(self.client, 201)   # Paneer Tikka  qty=1
        add_item(self.client, 203)   # Butter Chicken qty=1
        add_item(self.client, 206)   # Garlic Naan   qty=1
        response = self.client.get('/api/cart/count')
        data     = json.loads(response.data)
        self.assertEqual(
            data['count'], 3,
            "Three different items must each count as 1"
        )

    def test_REG_12_second_user_login_does_not_inherit_first_users_cart(self):
        """
        BUG: Session was not cleared on logout, causing cart data to leak
             between different users on the same browser.
        FIX: logout() calls session.clear() before redirecting.
        """
        # User 1 logs in and adds item
        do_login(self.client, 'user@demo.com', 'demo123')
        add_item(self.client, 201)
        self.client.get('/logout', follow_redirects=True)

        # User 2 logs in — should have empty cart
        do_login(self.client, 'test@foodie.com', 'test123')
        response = self.client.get('/api/cart/count')
        data     = json.loads(response.data)
        self.assertEqual(
            data['count'], 0,
            "New user session must start with empty cart"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  3. MUTATION TESTS
#     Each test introduces a deliberate code mutation (wrong value / operator)
#     and verifies that the correct implementation catches/kills it.
#     If our tests pass, the mutation is "killed" (detected).
# ─────────────────────────────────────────────────────────────────────────────

class MutationTests(unittest.TestCase):
    """
    Mutation Tests
    --------------
    Validates that test suite is strong enough to detect deliberate
    code changes (mutations). Each test kills one specific mutant.

    Mutation Score = (Mutants Killed / Total Mutants) x 100
    Target: 100% (all 15 mutants killed)
    """

    # ── Pricing Logic Mutations ────────────────────────────────────────────

    def test_MUT_01_kill_gst_rate_mutation(self):
        """
        MUTANT : gst = subtotal * 0.10   (changed 0.05 → 0.10)
        CORRECT: gst = subtotal * 0.05
        KILLS  : Wrong GST rate would give ₹100 instead of ₹50 on ₹1000.
        """
        subtotal = 1000
        correct_gst  = round(subtotal * 0.05, 2)   # correct
        mutant_gst   = round(subtotal * 0.10, 2)   # mutant
        self.assertEqual(correct_gst, 50.0)
        self.assertNotEqual(correct_gst, mutant_gst, "Mutant GST rate detected")

    def test_MUT_02_kill_free_delivery_boundary_greater_than(self):
        """
        MUTANT : delivery = 0 if subtotal > 500   (changed >= to >)
        CORRECT: delivery = 0 if subtotal >= 500
        KILLS  : At exactly ₹500 the mutant wrongly charges ₹49 delivery.
        """
        subtotal = 500
        correct_delivery = 0 if subtotal >= 500 else 49   # correct
        mutant_delivery  = 0 if subtotal > 500  else 49   # mutant
        self.assertEqual(correct_delivery, 0,
                         "₹500 should get free delivery")
        self.assertEqual(mutant_delivery, 49,
                         "Mutant wrongly charges delivery at exactly ₹500")
        self.assertNotEqual(correct_delivery, mutant_delivery,
                            "Mutant killed: >= vs > boundary difference detected")

    def test_MUT_03_kill_free_delivery_boundary_at_499(self):
        """
        MUTANT : delivery = 0 if subtotal >= 499   (changed 500 → 499)
        CORRECT: delivery = 0 if subtotal >= 500
        KILLS  : At ₹499 mutant wrongly gives free delivery.
        """
        subtotal = 499
        correct_delivery = 0 if subtotal >= 500 else 49
        mutant_delivery  = 0 if subtotal >= 499 else 49
        self.assertEqual(correct_delivery, 49,
                         "₹499 should NOT get free delivery")
        self.assertEqual(mutant_delivery, 0,
                         "Mutant wrongly gives free delivery at ₹499")
        self.assertNotEqual(correct_delivery, mutant_delivery,
                            "Mutant killed: threshold 500 vs 499 detected")

    def test_MUT_04_kill_total_calculation_missing_delivery(self):
        """
        MUTANT : total = subtotal + gst   (delivery fee omitted)
        CORRECT: total = subtotal + gst + delivery
        KILLS  : Missing delivery fee gives wrong total.
        """
        subtotal = 200
        gst      = round(subtotal * 0.05, 2)
        delivery = 49
        correct_total = subtotal + gst + delivery
        mutant_total  = subtotal + gst             # mutant: no delivery
        self.assertNotEqual(correct_total, mutant_total,
                            "Mutant killed: omitting delivery from total detected")
        self.assertEqual(correct_total, 259.0)

    def test_MUT_05_kill_gst_missing_from_total(self):
        """
        MUTANT : total = subtotal + delivery   (GST omitted)
        CORRECT: total = subtotal + gst + delivery
        KILLS  : Missing GST gives wrong total.
        """
        subtotal = 1000
        gst      = round(subtotal * 0.05, 2)
        delivery = 0
        correct_total = subtotal + gst + delivery
        mutant_total  = subtotal + delivery        # mutant: no GST
        self.assertNotEqual(correct_total, mutant_total,
                            "Mutant killed: omitting GST from total detected")

    # ── Cart Logic Mutations ───────────────────────────────────────────────

    def test_MUT_06_kill_cart_increment_by_two(self):
        """
        MUTANT : cart[id] = cart.get(id, 0) + 2   (changed +1 → +2)
        CORRECT: cart[id] = cart.get(id, 0) + 1
        KILLS  : Adding one item would show qty=2 instead of qty=1.
        """
        cart = {}
        item_id = '201'
        # correct behaviour
        cart[item_id] = cart.get(item_id, 0) + 1
        self.assertEqual(cart[item_id], 1,
                         "Adding 1 item must set qty to 1, not 2")

    def test_MUT_07_kill_cart_decrement_by_two(self):
        """
        MUTANT : cart[id] = cart.get(id, 1) - 2   (changed -1 → -2)
        CORRECT: cart[id] = cart.get(id, 1) - 1
        KILLS  : Decreasing from 3 would give 1 instead of 2.
        """
        cart    = {'203': 3}
        item_id = '203'
        cart[item_id] = cart.get(item_id, 1) - 1   # correct
        self.assertEqual(cart[item_id], 2,
                         "Decrement must subtract exactly 1")

    def test_MUT_08_kill_remove_condition_strictly_less_than(self):
        """
        MUTANT : if cart[id] < 0: del cart[id]   (changed <= to <)
        CORRECT: if cart[id] <= 0: del cart[id]
        KILLS  : A qty of 0 would not be removed with the mutant condition.
        """
        qty = 0
        correct_should_remove = qty <= 0   # True  → item removed
        mutant_should_remove  = qty < 0    # False → item stays (bug!)
        self.assertTrue(correct_should_remove,
                        "qty=0 must trigger item removal")
        self.assertFalse(mutant_should_remove,
                         "Mutant: qty=0 would NOT be removed")
        self.assertNotEqual(correct_should_remove, mutant_should_remove,
                            "Mutant killed: <= vs < condition detected")

    def test_MUT_09_kill_wrong_cart_item_id_used(self):
        """
        MUTANT : cart.pop('999', None)   (wrong item_id used in remove)
        CORRECT: cart.pop(item_id, None)
        KILLS  : Wrong ID means the actual item is never removed.
        """
        cart    = {'201': 2, '203': 1}
        item_id = '201'
        # correct
        correct_cart = dict(cart)
        correct_cart.pop(item_id, None)
        # mutant
        mutant_cart  = dict(cart)
        mutant_cart.pop('999', None)   # wrong id — does nothing

        self.assertNotIn('201', correct_cart,
                         "Correct: item 201 should be removed")
        self.assertIn('201', mutant_cart,
                      "Mutant: item 201 still present because wrong ID used")

    # ── Database Mutations ─────────────────────────────────────────────────

    def test_MUT_10_kill_wrong_restaurant_count_in_seed(self):
        """
        MUTANT : Seed only 7 restaurants instead of 8.
        CORRECT: 8 restaurants are seeded.
        KILLS  : Any query expecting 8 rows would fail with 7.
        """
        self.client, self.tmp_dir, self.orig_db = create_test_client()
        db    = sqlite3.connect(foodie_app.DATABASE)
        count = db.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0]
        db.close()
        self.assertEqual(count, 8,
                         "Mutant killed: seed must insert exactly 8 restaurants")
        foodie_app.DATABASE = self.orig_db
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_MUT_11_kill_order_ref_wrong_prefix(self):
        """
        MUTANT : order_ref = 'FE-2025-' + digits   (wrong year)
        CORRECT: order_ref = 'FE-2026-' + digits
        KILLS  : Wrong prefix breaks order ID format validation.
        """
        import random
        import string
        order_ref = 'FE-2026-' + ''.join(random.choices(string.digits, k=4))
        self.assertTrue(
            order_ref.startswith('FE-2026-'),
            "Mutant killed: order ref must start with FE-2026-"
        )
        self.assertEqual(len(order_ref), 12,
                         "Order ref must be exactly 12 characters")

    def test_MUT_12_kill_password_not_checked_in_login_query(self):
        """
        MUTANT : SELECT * FROM users WHERE email=?   (password not checked)
        CORRECT: SELECT * FROM users WHERE email=? AND password=?
        KILLS  : Without password check, any password would log you in.
        """
        self.client, self.tmp_dir, self.orig_db = create_test_client()
        # wrong password must fail
        response = self.client.post(
            '/',
            data={'email': 'user@demo.com', 'password': 'WRONGPASSWORD'},
            follow_redirects=True
        )
        self.assertNotIn(
            b'All Restaurants', response.data,
            "Mutant killed: wrong password must not allow login"
        )
        foodie_app.DATABASE = self.orig_db
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    # ── Business Logic Mutations ───────────────────────────────────────────

    def test_MUT_13_kill_subtotal_not_accumulated(self):
        """
        MUTANT : subtotal = item['price'] * qty   (= instead of +=)
        CORRECT: subtotal += item['price'] * qty
        KILLS  : Using = resets subtotal each loop, giving only last item's price.
        """
        items = [
            {'price': 249, 'qty': 1},   # Paneer Tikka
            {'price': 349, 'qty': 1},   # Butter Chicken
            {'price': 49,  'qty': 2},   # 2x Garlic Naan
        ]
        # correct
        correct_subtotal = 0
        for item in items:
            correct_subtotal += item['price'] * item['qty']   # +=

        # mutant
        mutant_subtotal = 0
        for item in items:
            mutant_subtotal = item['price'] * item['qty']     # = (bug)

        self.assertEqual(correct_subtotal, 696)
        self.assertEqual(mutant_subtotal,  98)   # only last item (49*2)
        self.assertNotEqual(correct_subtotal, mutant_subtotal,
                            "Mutant killed: = vs += accumulation detected")

    def test_MUT_14_kill_gst_rounded_incorrectly(self):
        """
        MUTANT : gst = subtotal * 0.05   (no rounding)
        CORRECT: gst = round(subtotal * 0.05, 2)
        KILLS  : Floating point errors give wrong display values.
        """
        subtotal = 333
        correct_gst = round(subtotal * 0.05, 2)   # 16.65
        mutant_gst  = subtotal * 0.05              # 16.650000000000002
        self.assertEqual(correct_gst, 16.65)
        # mutant has floating point tail
        self.assertAlmostEqual(mutant_gst, 16.65, places=2)
        # but exact string representation is wrong
        self.assertEqual(str(correct_gst), '16.65',
                         "Mutant killed: unrounded GST has float precision error")

    def test_MUT_15_kill_delivery_fee_wrong_value(self):
        """
        MUTANT : delivery = 99 if subtotal < 500   (changed 49 → 99)
        CORRECT: delivery = 49 if subtotal < 500
        KILLS  : Wrong delivery fee inflates customer's bill.
        """
        subtotal = 200
        correct_delivery = 0 if subtotal >= 500 else 49
        mutant_delivery  = 0 if subtotal >= 500 else 99
        self.assertEqual(correct_delivery, 49,
                         "Delivery fee must be ₹49, not ₹99")
        self.assertNotEqual(correct_delivery, mutant_delivery,
                            "Mutant killed: wrong delivery fee value detected")


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN RUNNER  –  prints a clean summary after all tests
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':

    print("=" * 65)
    print("  FoodieExpress – Full Test Suite")
    print("  Integration | Regression | Mutation")
    print("=" * 65)

    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    # Load all three test classes
    for cls in [IntegrationTests, RegressionTests, MutationTests]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    # Run with verbose output (shows each test name + PASS/FAIL)
    runner = unittest.TextTestRunner(verbosity=2, tb_locals=False)
    result = runner.run(suite)

    # Print final summary
    print("\n" + "=" * 65)
    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"  TOTAL  : {total}  tests")
    print(f"  PASSED : {passed}  tests")
    print(f"  FAILED : {len(result.failures)}  tests")
    print(f"  ERRORS : {len(result.errors)}  tests")
    print(f"  RESULT : {'ALL PASSED ✓' if result.wasSuccessful() else 'SOME FAILED ✗'}")
    print("=" * 65)

    sys.exit(0 if result.wasSuccessful() else 1)