"""
FoodieExpress – Flask app with SQLite database integration
"""
import sqlite3, os, json, random, string
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, g)

app = Flask(__name__)
app.secret_key = "demo_secret_key_123"

DATABASE = os.path.join(os.path.dirname(__file__), 'foodieexpress.db')

# ─────────────────────────────  DB Helpers  ──────────────────────────────────

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid

# ─────────────────────────────  DB Init  ─────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT    UNIQUE NOT NULL,
    password    TEXT    NOT NULL,
    name        TEXT    NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS restaurants (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    cuisine     TEXT    NOT NULL,
    rating      REAL    NOT NULL,
    delivery_time TEXT  NOT NULL,
    min_order   INTEGER NOT NULL,
    image_url   TEXT    NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS menu_items (
    id            INTEGER PRIMARY KEY,
    restaurant_id INTEGER NOT NULL,
    name          TEXT    NOT NULL,
    category      TEXT    NOT NULL,
    price         INTEGER NOT NULL,
    is_veg        INTEGER NOT NULL DEFAULT 1,
    image_url     TEXT,
    description   TEXT,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
);

CREATE TABLE IF NOT EXISTS orders (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    order_ref    TEXT    NOT NULL,
    user_id      INTEGER NOT NULL,
    items_json   TEXT    NOT NULL,
    subtotal     REAL    NOT NULL,
    gst          REAL    NOT NULL,
    delivery_fee REAL    NOT NULL,
    total        REAL    NOT NULL,
    full_name    TEXT,
    address      TEXT,
    payment_method TEXT,
    status       TEXT    DEFAULT 'placed',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

SEED_RESTAURANTS = [
    (1,'Bella Italia','Italian',4.5,'30-40 min',199,
     'https://images.pexels.com/photos/262978/pexels-photo-262978.jpeg?w=600&h=400&fit=crop',
     'Authentic Italian flavours crafted with love'),
    (2,'Spice Garden','Indian',4.7,'25-35 min',149,
     'https://images.pexels.com/photos/8684077/pexels-photo-8684077.jpeg?w=600&h=400&fit=crop',
     'Rich curries and tandoor specials from the heart of India'),
    (3,'Dragon Wok','Chinese',4.3,'35-45 min',179,
     'https://images.pexels.com/photos/955137/pexels-photo-955137.jpeg?w=600&h=400&fit=crop',
     'Wok-tossed perfection with bold Asian sauces'),
    (4,'Taco Fiesta','Mexican',4.6,'20-30 min',129,
     'https://images.pexels.com/photos/36498696/pexels-photo-36498696.jpeg?w=600&h=400&fit=crop',
     'Street-style tacos and vibrant Mexican bowls'),
    (5,'Burger Barn','American',4.4,'20-30 min',99,
     'https://images.pexels.com/photos/1639557/pexels-photo-1639557.jpeg?w=600&h=400&fit=crop',
     'Juicy smash burgers and crispy fries done right'),
    (6,'Sushi Zen','Japanese',4.8,'40-50 min',299,
     'https://images.pexels.com/photos/1148086/pexels-photo-1148086.jpeg?w=600&h=400&fit=crop',
     'Omakase-inspired sushi rolls and ramen bowls'),
    (7,'Kerala Kitchen','South Indian',4.5,'30-40 min',149,
     'https://images.pexels.com/photos/9609857/pexels-photo-9609857.jpeg?w=600&h=400&fit=crop',
     'Coastal curries, appam, and fresh seafood delights'),
    (8,'The Dessert Lab','Desserts',4.9,'15-25 min',79,
     'https://images.pexels.com/photos/1126359/pexels-photo-1126359.jpeg?w=600&h=400&fit=crop',
     'Artisanal desserts, waffles, and ice cream creations'),
]

SEED_MENU = [
    # Bella Italia
    (101,1,'Bruschetta al Pomodoro','Starters',199,1,
     'https://images.pexels.com/photos/36933464/pexels-photo-36933464.jpeg?w=400&h=300&fit=crop',
     'Toasted bread with fresh tomatoes, basil, and extra-virgin olive oil'),
    (102,1,'Arancini di Riso','Starters',249,1,
     'https://images.pexels.com/photos/34692571/pexels-photo-34692571.jpeg?w=400&h=300&fit=crop',
     'Crispy fried risotto balls filled with mozzarella'),
    (103,1,'Spaghetti Carbonara','Main Course',399,0,
     'https://images.pexels.com/photos/722670/spaghetti-bolognese-food-rustic-722670.jpeg?w=400&h=300&fit=crop',
     'Classic Roman pasta with egg, pecorino, guanciale, and black pepper'),
    (104,1,'Margherita Pizza','Main Course',349,1,
     'https://images.pexels.com/photos/2147491/pexels-photo-2147491.jpeg?w=400&h=300&fit=crop',
     'San Marzano tomato, fior di latte mozzarella, fresh basil'),
    (105,1,'Penne Arrabbiata','Main Course',299,1,
     'https://images.pexels.com/photos/5211210/pexels-photo-5211210.jpeg?w=400&h=300&fit=crop',
     'Spicy tomato sauce, garlic, red chilli flakes, fresh herbs'),
    (106,1,'Tiramisu','Desserts',199,1,
     'https://images.pexels.com/photos/6880219/pexels-photo-6880219.jpeg?w=400&h=300&fit=crop',
     'Classic Italian mascarpone dessert with espresso-soaked ladyfingers'),
    # Spice Garden
    (201,2,'Paneer Tikka','Starters',249,1,
     'https://images.pexels.com/photos/33430558/pexels-photo-33430558.jpeg?w=400&h=300&fit=crop',
     'Char-grilled cottage cheese with peppers and aromatic spices'),
    (202,2,'Hara Bhara Kebab','Starters',199,1,
     'https://images.pexels.com/photos/7301037/pexels-photo-7301037.jpeg?w=400&h=300&fit=crop',
     'Spinach and green pea patties with mint chutney'),
    (203,2,'Butter Chicken','Main Course',349,0,
     'https://images.pexels.com/photos/7625056/pexels-photo-7625056.jpeg?w=400&h=300&fit=crop',
     'Tender chicken in rich, velvety tomato-butter-cream gravy'),
    (204,2,'Hyderabadi Biryani','Main Course',299,0,
     'https://images.pexels.com/photos/12737656/pexels-photo-12737656.jpeg?w=400&h=300&fit=crop',
     'Slow-cooked basmati rice with succulent mutton and saffron'),
    (205,2,'Dal Makhani','Main Course',249,1,
     'https://images.pexels.com/photos/28674710/pexels-photo-28674710.jpeg?w=400&h=300&fit=crop',
     'Overnight slow-cooked black lentils with butter and cream'),
    (206,2,'Garlic Naan','Breads',49,1,
     'https://images.pexels.com/photos/1117862/pexels-photo-1117862.jpeg?w=400&h=300&fit=crop',
     'Soft tandoor-baked flatbread with garlic and butter'),
    (207,2,'Gulab Jamun','Desserts',129,1,
     'https://images.pexels.com/photos/6896577/pexels-photo-6896577.jpeg?w=400&h=300&fit=crop',
     'Soft milk-solid balls soaked in rose-cardamom sugar syrup'),
    (208,2,'Mango Lassi','Beverages',99,1,
     'https://images.pexels.com/photos/14509267/pexels-photo-14509267.jpeg?w=400&h=300&fit=crop',
     'Chilled yoghurt drink blended with Alphonso mango'),
    # Dragon Wok
    (301,3,'Spring Rolls','Starters',149,1,
     'https://images.pexels.com/photos/4001867/pexels-photo-4001867.jpeg?w=400&h=300&fit=crop',
     'Crispy vegetable rolls with sweet chilli dipping sauce'),
    (302,3,'Wonton Soup','Starters',179,0,
     'https://images.pexels.com/photos/955137/pexels-photo-955137.jpeg?w=400&h=300&fit=crop',
     'Silky pork dumplings in a clear ginger-garlic broth'),
    (303,3,'Kung Pao Chicken','Main Course',299,0,
     'https://images.pexels.com/photos/2338407/pexels-photo-2338407.jpeg?w=400&h=300&fit=crop',
     'Stir-fried chicken with peanuts and Sichuan chillies'),
    (304,3,'Veg Fried Rice','Main Course',199,1,
     'https://images.pexels.com/photos/35071826/pexels-photo-35071826.jpeg?w=400&h=300&fit=crop',
     'Wok-tossed rice with seasonal vegetables and soy sauce'),
    (305,3,'Hakka Noodles','Main Course',219,1,
     'https://images.pexels.com/photos/1907244/pexels-photo-1907244.jpeg?w=400&h=300&fit=crop',
     'Hand-pulled noodles stir-fried with vegetables and schezwan sauce'),
    # Taco Fiesta
    (401,4,'Guacamole & Chips','Starters',149,1,
     'https://images.pexels.com/photos/4562973/pexels-photo-4562973.jpeg?w=400&h=300&fit=crop',
     'House-made guacamole with crispy tortilla chips'),
    (402,4,'Chicken Tacos','Main Course',249,0,
     'https://images.pexels.com/photos/461198/pexels-photo-461198.jpeg?w=400&h=300&fit=crop',
     'Grilled chicken in soft corn tortillas with salsa and sour cream'),
    (403,4,'Veggie Burrito','Main Course',219,1,
     'https://images.pexels.com/photos/4958641/pexels-photo-4958641.jpeg?w=400&h=300&fit=crop',
     'Flour tortilla stuffed with beans, rice, cheese, and fresh salsa'),
    (404,4,'Churros','Desserts',129,1,
     'https://images.pexels.com/photos/6310077/pexels-photo-6310077.jpeg?w=400&h=300&fit=crop',
     'Crispy fried dough sticks rolled in cinnamon sugar with chocolate sauce'),
    # Burger Barn
    (501,5,'Classic Smash Burger','Main Course',259,0,
     'https://images.pexels.com/photos/1639557/pexels-photo-1639557.jpeg?w=400&h=300&fit=crop',
     'Double smash patty, American cheese, pickles, mustard'),
    (502,5,'Crispy Chicken Burger','Main Course',229,0,
     'https://images.pexels.com/photos/2271107/pexels-photo-2271107.jpeg?w=400&h=300&fit=crop',
     'Fried chicken thigh, coleslaw, sriracha mayo on a brioche bun'),
    (503,5,'Loaded Fries','Starters',149,1,
     'https://images.pexels.com/photos/1583884/pexels-photo-1583884.jpeg?w=400&h=300&fit=crop',
     'Thick-cut fries loaded with cheese sauce and jalapeños'),
    (504,5,'Oreo Milkshake','Beverages',149,1,
     'https://images.pexels.com/photos/3727250/pexels-photo-3727250.jpeg?w=400&h=300&fit=crop',
     'Thick vanilla shake blended with crushed Oreo cookies'),
    # Sushi Zen
    (601,6,'Dragon Roll','Main Course',449,0,
     'https://images.pexels.com/photos/1148086/pexels-photo-1148086.jpeg?w=400&h=300&fit=crop',
     'Shrimp tempura, cucumber, avocado, tobiko'),
    (602,6,'Avocado Roll','Main Course',299,1,
     'https://images.pexels.com/photos/18891321/pexels-photo-18891321.jpeg?w=400&h=300&fit=crop',
     'Fresh avocado, cucumber, sesame seeds, soy paper'),
    (603,6,'Miso Soup','Starters',99,1,
     'https://images.pexels.com/photos/13065217/pexels-photo-13065217.jpeg?w=400&h=300&fit=crop',
     'Classic dashi broth with tofu, wakame, and spring onion'),
    (604,6,'Matcha Latte','Beverages',149,1,
     'https://images.pexels.com/photos/10770322/pexels-photo-10770322.jpeg?w=400&h=300&fit=crop',
     'Ceremonial grade matcha whisked with steamed oat milk'),
    # Kerala Kitchen
    (701,7,'Fish Molee','Main Course',349,0,
     'https://images.pexels.com/photos/35532834/pexels-photo-35532834.jpeg?w=400&h=300&fit=crop',
     'Coastal fish curry in fragrant coconut milk and turmeric'),
    (702,7,'Appam & Stew','Main Course',199,1,
     'https://images.pexels.com/photos/30622221/pexels-photo-30622221.jpeg?w=400&h=300&fit=crop',
     'Lacy rice hoppers with mild vegetable stew'),
    (703,7,'Banana Chips','Starters',79,1,
     'https://images.pexels.com/photos/30622220/pexels-photo-30622220.jpeg?w=400&h=300&fit=crop',
     'Crispy raw banana chips fried in coconut oil'),
    (704,7,'Tender Coconut Water lassi','Beverages',69,1,
     'https://images.pexels.com/photos/15522898/pexels-photo-15522898.jpeg?w=400&h=300&fit=crop',
     'Fresh served straight from the shell'),
    # The Dessert Lab
    (801,8,'Belgian Waffle','Desserts',199,1,
     'https://images.pexels.com/photos/6529788/pexels-photo-6529788.jpeg?w=400&h=300&fit=crop',
     'Crispy waffle with Nutella, banana, and vanilla ice cream'),
    (802,8,'Lava Cake','Desserts',179,1,
     'https://images.pexels.com/photos/36270708/pexels-photo-36270708.jpeg?w=400&h=300&fit=crop',
     'Warm chocolate cake with a gooey molten centre'),
    (803,8,'Gelato Trio','Desserts',149,1,
     'https://images.pexels.com/photos/23531335/pexels-photo-23531335.jpeg?w=400&h=300&fit=crop',
     'Three scoops of artisanal gelato – pick your flavours'),
    (804,8,'Cold Brew','Beverages',129,1,
     'https://images.pexels.com/photos/13735966/pexels-photo-13735966.jpeg?w=400&h=300&fit=crop',
     '12-hour cold-steeped Ethiopian coffee'),
]

def init_db():
    """Create tables and seed data if the DB is fresh."""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    # Seed only if empty
    if not db.execute("SELECT 1 FROM restaurants LIMIT 1").fetchone():
        db.executemany(
            "INSERT INTO restaurants VALUES (?,?,?,?,?,?,?,?)", SEED_RESTAURANTS)
        db.executemany(
            "INSERT INTO menu_items VALUES (?,?,?,?,?,?,?,?)", SEED_MENU)
    # Ensure demo user exists
    if not db.execute("SELECT 1 FROM users WHERE email=?",
                      ('user@demo.com',)).fetchone():
        db.execute("INSERT INTO users (email,password,name) VALUES (?,?,?)",
                   ('user@demo.com', 'demo123', 'Ramesh Kumar'))
        db.execute("INSERT INTO users (email,password,name) VALUES (?,?,?)",
                   ('test@foodie.com', 'test123', 'Priya Sharma'))
    db.commit()
    db.close()

# ─────────────────────────────  Auth  ────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────  Routes  ──────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        user = query_db("SELECT * FROM users WHERE email=? AND password=?",
                        (email, password), one=True)
        if user:
            session['user'] = {'id': user['id'], 'email': user['email'],
                               'name': user['name']}
            session['cart'] = {}
            return redirect(url_for('restaurants'))
        error = 'Invalid email or password. Try user@demo.com / demo123'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/restaurants')
@login_required
def restaurants():
    rows = query_db("SELECT * FROM restaurants ORDER BY rating DESC")
    rests = [dict(r) for r in rows]
    return render_template('restaurants.html', restaurants=rests,
                           user=session['user'])

@app.route('/menu/<int:restaurant_id>')
@login_required
def menu(restaurant_id):
    restaurant = query_db("SELECT * FROM restaurants WHERE id=?",
                           (restaurant_id,), one=True)
    if not restaurant:
        return redirect(url_for('restaurants'))
    restaurant = dict(restaurant)
    items_raw = query_db(
        "SELECT * FROM menu_items WHERE restaurant_id=? ORDER BY category,name",
        (restaurant_id,))
    items = [dict(i) for i in items_raw]
    categories = ['All'] + sorted(set(i['category'] for i in items))
    cart = session.get('cart', {})
    return render_template('menu.html', restaurant=restaurant, items=items,
                           categories=categories, cart=cart,
                           user=session['user'])

@app.route('/cart')
@login_required
def cart():
    cart   = session.get('cart', {})
    cart_items, subtotal = _build_cart_items(cart)
    gst      = round(subtotal * 0.05, 2)
    delivery = 0 if subtotal >= 500 else 49
    total    = subtotal + gst + delivery
    return render_template('cart.html', cart_items=cart_items,
                           subtotal=subtotal, gst=gst,
                           delivery=delivery, total=total,
                           user=session['user'])

@app.route('/api/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    item_id = str(request.json.get('item_id'))
    cart = session.get('cart', {})
    cart[item_id] = cart.get(item_id, 0) + 1
    session['cart'] = cart
    session.modified = True
    return jsonify({'success': True, 'qty': cart[item_id],
                    'cart_count': sum(cart.values())})

@app.route('/api/cart/update', methods=['POST'])
@login_required
def update_cart():
    data    = request.json
    item_id = str(data.get('item_id'))
    action  = data.get('action')
    cart    = session.get('cart', {})
    if action == 'increase':
        cart[item_id] = cart.get(item_id, 0) + 1
    elif action == 'decrease':
        cart[item_id] = cart.get(item_id, 1) - 1
        if cart[item_id] <= 0:
            del cart[item_id]
    elif action == 'remove':
        cart.pop(item_id, None)
    session['cart'] = cart
    session.modified = True
    return jsonify({'success': True, 'cart_count': sum(cart.values())})

@app.route('/api/cart/count')
@login_required
def cart_count():
    return jsonify({'count': sum(session.get('cart', {}).values())})

@app.route('/checkout', methods=['GET'])
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('cart'))
    cart_items, subtotal = _build_cart_items(cart)
    gst      = round(subtotal * 0.05, 2)
    delivery = 0 if subtotal >= 500 else 49
    total    = subtotal + gst + delivery
    return render_template('checkout.html', cart_items=cart_items,
                           subtotal=subtotal, gst=gst,
                           delivery=delivery, total=total,
                           user=session['user'])

@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('cart'))
    cart_items, subtotal = _build_cart_items(cart)
    gst      = round(subtotal * 0.05, 2)
    delivery = 0 if subtotal >= 500 else 49
    total    = subtotal + gst + delivery
    order_ref = 'FE-2026-' + ''.join(random.choices(string.digits, k=4))
    name    = request.form.get('full_name', session['user']['name'])
    address = (f"{request.form.get('house','')}, "
               f"{request.form.get('area','')}, "
               f"{request.form.get('city','Chennai')} "
               f"{request.form.get('pincode','')}")
    execute_db(
        """INSERT INTO orders
           (order_ref,user_id,items_json,subtotal,gst,delivery_fee,
            total,full_name,address,payment_method)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (order_ref, session['user']['id'], json.dumps(cart_items),
         subtotal, gst, delivery, total, name, address,
         request.form.get('payment','upi')))
    session['cart'] = {}
    session.modified = True
    return render_template('success.html', order_id=order_ref,
                           cart_items=cart_items, subtotal=subtotal,
                           gst=gst, delivery=delivery, total=total,
                           name=name, address=address,
                           user=session['user'])

# ─────────────────────────────  Helpers  ─────────────────────────────────────

def _build_cart_items(cart):
    """Return (list_of_cart_dicts, subtotal) from session cart."""
    items, subtotal = [], 0
    for item_id, qty in cart.items():
        row = query_db("SELECT m.*, r.name AS restaurant_name "
                       "FROM menu_items m "
                       "JOIN restaurants r ON r.id = m.restaurant_id "
                       "WHERE m.id=?", (item_id,), one=True)
        if row:
            d = dict(row)
            d['qty']        = qty
            d['total']      = d['price'] * qty
            d['restaurant'] = d['restaurant_name']
            # safety aliases so templates work regardless of column name used
            d.setdefault('image_url', d.get('image', ''))
            items.append(d)
            subtotal += d['total']
    return items, subtotal

# ─────────────────────────────  Main  ────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
