import streamlit as st
import pandas as pd
from models.inventory import POSSystem
from models.users import Manager

st.set_page_config(page_title="Point of Sale", layout="wide")
st.title("Point of Sale Terminal")

if "current_user" not in st.session_state or st.session_state.current_user is None:
    st.warning("Access Denied. Please log in from the Home page first.")
    st.stop()

current_user = st.session_state.current_user
user_role = current_user.role


def init_shopping_cart():
    if "cart" not in st.session_state:
        st.session_state.cart = []
    if "cart_total" not in st.session_state:
        st.session_state.cart_total = 0.0


def update_cart_total():
    st.session_state.cart_total = sum(item["line_total"] for item in st.session_state.cart)


def add_to_cart(product_id, product_name, quantity, unit_price):
    for item in st.session_state.cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["line_total"] = item["quantity"] * item["unit_price"]
            update_cart_total()
            return

    st.session_state.cart.append(
        {
            "product_id": product_id,
            "product_name": product_name,
            "quantity": quantity,
            "unit_price": float(unit_price),
            "line_total": float(quantity * unit_price),
        }
    )
    update_cart_total()


def remove_from_cart(product_id):
    st.session_state.cart = [item for item in st.session_state.cart if item["product_id"] != product_id]
    update_cart_total()


def clear_cart():
    st.session_state.cart = []
    st.session_state.cart_total = 0.0


# Initialize shopping cart
init_shopping_cart()

# Custom CSS for POS interface
st.markdown("""
<style>
    .pos-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .cart-item {
        background: white;
        padding: 0.75rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border: 1px solid #dee2e6;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .total-display {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        font-size: 1.5em;
        font-weight: bold;
        margin: 1rem 0;
    }
    .product-button {
        background: #007bff;
        color: white;
        border: none;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        cursor: pointer;
        margin: 0.25rem;
        width: 100%;
        text-align: left;
    }
    .product-button:hover {
        background: #0056b3;
    }
    .manager-override {
        background: #ffc107;
        color: #212529;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 2px solid #ffca2c;
    }
</style>
""", unsafe_allow_html=True)

# Layout: Products | Cart | Checkout
col1, col2, col3 = st.columns([2, 2, 1])

# Column 1: Product Selection
with col1:
    st.markdown("<div class='pos-container'>", unsafe_allow_html=True)
    st.subheader("Product Selection")

    # Product search/filter
    search_term = st.text_input("Search products", placeholder="Type to search...")

    # Get available products
    products = POSSystem.get_products_for_sale()

    if products:
        # Filter products based on search
        if search_term:
            filtered_products = [p for p in products if search_term.lower() in p["productname"].lower()]
        else:
            filtered_products = products

        # Display products in a grid
        for product in filtered_products[:20]:  # Limit to 20 for performance
            if st.button(
                f"{product['productname']} - ZMW {float(product['sellingprice']):.2f}",
                key=f"prod_{product['productid']}",
                help=f"Stock: {product['stock']} units available"
            ):
                add_to_cart(product["productid"], product["productname"], 1, float(product["sellingprice"]))
                st.rerun()

        if len(filtered_products) > 20:
            st.info(f"Showing first 20 of {len(filtered_products)} products")
    else:
        st.warning("No products available for sale")

    st.markdown("</div>", unsafe_allow_html=True)

# Column 2: Shopping Cart
with col2:
    st.markdown("<div class='pos-container'>", unsafe_allow_html=True)
    st.subheader("Shopping Cart")

    cart_items = st.session_state.get('cart', [])

    if cart_items:
        for idx, item in enumerate(cart_items):
            col_a, col_b, col_c = st.columns([3, 1, 1])
            with col_a:
                st.write(f"**{item['product_name']}**")
            with col_b:
                # Quantity adjustment
                new_qty = st.number_input(
                    "Qty",
                    min_value=1,
                    value=item['quantity'],
                    key=f"qty_{idx}",
                    label_visibility="collapsed"
                )
                if new_qty != item['quantity']:
                    item['quantity'] = new_qty
                    item['line_total'] = new_qty * item['unit_price']
                    update_cart_total()
                    st.rerun()
            with col_c:
                if st.button("❌", key=f"remove_{idx}", help="Remove item"):
                    remove_from_cart(item['product_id'])
                    st.rerun()

            st.write(f"@{item['unit_price']:.2f} = ZMW {item['line_total']:.2f}")
            st.markdown("---")

        # Cart actions
        col_clear, col_discount = st.columns(2)
        with col_clear:
            if st.button("Clear Cart", type="secondary"):
                clear_cart()
                st.rerun()
        with col_discount:
            # Manager override for discounts
            if user_role.lower() == "manager":
                discount_pct = st.number_input("Discount %", min_value=0.0, max_value=100.0, value=0.0, step=5.0)
            else:
                discount_pct = 0.0

    else:
        st.info("Cart is empty. Select products to add them here.")

    st.markdown("</div>", unsafe_allow_html=True)

# Column 3: Checkout
with col3:
    st.markdown("<div class='pos-container'>", unsafe_allow_html=True)
    st.subheader("Checkout")

    cart_total = st.session_state.get('cart_total', 0.0)
    discount_amount = cart_total * (discount_pct / 100) if 'discount_pct' in locals() else 0
    final_total = cart_total - discount_amount

    # Total display
    st.markdown(f"""
    <div class='total-display'>
        Subtotal: ZMW {cart_total:.2f}<br>
        {'Discount: ZMW ' + f'{discount_amount:.2f}' if discount_amount > 0 else ''}<br>
        Total: ZMW {final_total:.2f}
    </div>
    """, unsafe_allow_html=True)

    # Payment method
    payment_method = st.selectbox("Payment Method", ["cash", "card", "mobile_money"])

    # Manager override for returns/removals
    if user_role.lower() != "manager" and len(cart_items) > 0:
        st.markdown("<div class='manager-override'>", unsafe_allow_html=True)
        st.markdown("**Manager Override Required**")
        override_code = st.text_input("Enter manager code", type="password", key="override")
        temp_manager = Manager(0, "override_check", "Override Check")
        if override_code and temp_manager.authorize_void(override_code):
            st.success("Override granted - you can now modify cart")
            allow_modifications = True
        else:
            allow_modifications = False
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        allow_modifications = True

    # Process sale
    if cart_items and final_total > 0:
        if st.button("Complete Sale", type="primary", use_container_width=True):
            try:
                sale_id = POSSystem.process_transaction(
                    cart_items=cart_items,
                    total_amount=final_total,
                    processed_by=current_user.user_id,
                    payment_method=payment_method,
                )
                st.success(f"Sale #{sale_id} processed successfully")
                # Print receipt (in real system, this would print)
                st.info("Receipt printed successfully")
                clear_cart()
                st.rerun()
            except Exception as exc:
                st.error(f"Error processing sale: {exc}")
    else:
        st.button("Complete Sale", type="primary", use_container_width=True, disabled=True)

    # Quick actions
    st.markdown("---")
    st.subheader("Quick Actions")

    if st.button("New Transaction", use_container_width=True):
        clear_cart()
        st.rerun()

    # Show current user info
    st.markdown("---")
    st.markdown(f"**Cashier:** {current_user.full_name}")
    st.markdown(f"**Role:** {user_role.title()}")

    st.markdown("</div>", unsafe_allow_html=True)

# Footer with cart summary
if cart_items:
    st.markdown("---")
    st.markdown(f"**Cart Summary:** {len(cart_items)} items | Total: ZMW {final_total:.2f}")
