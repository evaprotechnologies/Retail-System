import psycopg2
import psycopg2.extras
import streamlit as st
import hashlib

@st.cache_resource
def init_connection():
    return psycopg2.connect(
        host="localhost",
        database="retailsystemdb",
        user="postgres",
        password="postgres",
        port="5432"
    )

def get_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    """Authenticate user and return user info if successful"""
    conn = init_connection()
    cursor = get_cursor(conn)

    try:
        hashed_password = hash_password(password)
        cursor.execute("""
            SELECT UserID, Username, FullName, Role, IsActive
            FROM Users
            WHERE Username = %s AND Password = %s AND IsActive = TRUE
        """, (username, password))  # Note: In production, compare with hashed password

        user = cursor.fetchone()
        if user:
            # Update last login
            cursor.execute("UPDATE Users SET LastLogin = CURRENT_TIMESTAMP WHERE UserID = %s", (user['userid'],))
            conn.commit()
            return dict(user)
        return None
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

def check_login(required_roles=None):
    """Security function to prevent accessing pages without proper login and role."""
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.warning("Access Denied. Please log in from the Home page first.")
        st.stop()

    if required_roles:
        user_role = st.session_state.get('user_role', '').lower()
        if user_role not in [role.lower() for role in required_roles]:
            st.error("Access Denied. This page requires Manager privileges.")
            st.info("Please contact your store manager for access.")
            st.stop()

def get_current_user():
    """Get current user information from session"""
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        return None

    return {
        'userid': st.session_state.get('userid'),
        'username': st.session_state.get('username'),
        'fullname': st.session_state.get('fullname'),
        'role': st.session_state.get('user_role')
    }

def init_shopping_cart():
    """Initialize shopping cart in session state"""
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    if 'cart_total' not in st.session_state:
        st.session_state.cart_total = 0.0

def add_to_cart(product_id, product_name, quantity, unit_price):
    """Add item to shopping cart"""
    init_shopping_cart()

    # Check if item already in cart
    for item in st.session_state.cart:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            item['line_total'] = item['quantity'] * item['unit_price']
            update_cart_total()
            return

    # Add new item
    st.session_state.cart.append({
        'product_id': product_id,
        'product_name': product_name,
        'quantity': quantity,
        'unit_price': unit_price,
        'line_total': quantity * unit_price
    })
    update_cart_total()

def remove_from_cart(product_id):
    """Remove item from shopping cart"""
    init_shopping_cart()
    st.session_state.cart = [item for item in st.session_state.cart if item['product_id'] != product_id]
    update_cart_total()

def update_cart_total():
    """Update total cart value"""
    st.session_state.cart_total = sum(item['line_total'] for item in st.session_state.cart)

def clear_cart():
    """Clear shopping cart"""
    st.session_state.cart = []
    st.session_state.cart_total = 0.0

def get_products_for_sale():
    """Get available products for sale"""
    conn = init_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute("""
            SELECT p.ProductID, p.ProductName, p.SellingPrice, COALESCE(s.QuantityAvailable, 0) as Stock
            FROM Products p
            LEFT JOIN Stock s ON p.ProductID = s.ProductID
            WHERE COALESCE(s.QuantityAvailable, 0) > 0
            ORDER BY p.ProductName
        """)
        return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching products: {e}")
        return []
    finally:
        conn.close()

def process_sale(cart_items, payment_method='cash'):
    """Process sale transaction"""
    if not cart_items:
        return False, "Cart is empty"

    conn = init_connection()
    cursor = get_cursor(conn)

    try:
        current_user = get_current_user()
        if not current_user:
            return False, "User not authenticated"

        # Calculate total
        total = sum(item['line_total'] for item in cart_items)

        # Insert sale
        cursor.execute("""
            INSERT INTO Sales (TotalAmount, ProcessedBy, PaymentMethod)
            VALUES (%s, %s, %s) RETURNING SaleID
        """, (total, current_user['userid'], payment_method))

        sale_id = cursor.fetchone()['saleid']

        # Insert sale details and update stock
        for item in cart_items:
            cursor.execute("""
                INSERT INTO Sales_Details (SaleID, ProductID, QuantitySold, UnitPrice, LineTotal)
                VALUES (%s, %s, %s, %s, %s)
            """, (sale_id, item['product_id'], item['quantity'], item['unit_price'], item['line_total']))

        conn.commit()
        return True, f"Sale #{sale_id} processed successfully"

    except Exception as e:
        conn.rollback()
        return False, f"Error processing sale: {e}"
    finally:
        conn.close()