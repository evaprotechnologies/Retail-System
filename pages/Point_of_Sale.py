import streamlit as st

from models.inventory import POSSystem
from models.invoice import InvoiceService
from models.navigation import render_sidebar
from models.store_settings import StoreSettings

st.set_page_config(page_title="Point of Sale", layout="wide", initial_sidebar_state="expanded")
render_sidebar()

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
    if "pos_removal_request" not in st.session_state:
        st.session_state.pos_removal_request = None
    if "barcode_scanner_nonce" not in st.session_state:
        st.session_state.barcode_scanner_nonce = 0
    if "pending_invoice_sale_id" not in st.session_state:
        st.session_state.pending_invoice_sale_id = None


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


def request_remove_line(product_id):
    if str(user_role).lower() == "manager":
        remove_from_cart(product_id)
        st.session_state.pos_removal_request = None
        st.rerun()
    st.session_state.pos_removal_request = {"action": "remove", "product_id": product_id}
    st.rerun()


def request_clear_cart():
    if str(user_role).lower() == "manager":
        clear_cart()
        st.session_state.pos_removal_request = None
        st.rerun()
    st.session_state.pos_removal_request = {"action": "clear"}
    st.rerun()


def try_lookup_barcode(code: str):
    prod = POSSystem.get_product_by_barcode(code)
    if not prod:
        st.error("Unknown barcode.")
        return
    qty = int(prod["quantityavailable"])
    if qty <= 0:
        st.error("Out of stock.")
        return
    add_to_cart(prod["productid"], prod["productname"], 1, float(prod["sellingprice"]))
    st.success(f"Added: {prod['productname']}")
    st.rerun()


init_shopping_cart()

st.title("Point of Sale Terminal")

pending_inv = st.session_state.pending_invoice_sale_id
if pending_inv:
    try:
        pdf_bytes = InvoiceService.get_pdf_for_user(int(pending_inv), current_user)
        st.success(f"Sale #{pending_inv} completed — customer invoice is ready.")
        c_dl, c_done = st.columns([1, 1])
        with c_dl:
            st.download_button(
                label="Download invoice (PDF)",
                data=pdf_bytes,
                file_name=f"invoice_{pending_inv}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
                key=f"dl_invoice_pos_{pending_inv}",
            )
        with c_done:
            if st.button("Dismiss (next customer)", use_container_width=True, key="dismiss_invoice_banner"):
                st.session_state.pending_invoice_sale_id = None
                st.rerun()
        with st.expander("View receipt on screen (same as PDF)", expanded=False):
            st.text(InvoiceService.format_receipt_text(int(pending_inv)))
    except PermissionError:
        st.session_state.pending_invoice_sale_id = None
    except Exception as exc:
        st.error(f"Could not build invoice: {exc}")
    st.divider()

st.markdown(
    """
<style>
    .pos-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
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
</style>
""",
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns([2, 2, 1])

products = POSSystem.get_products_for_sale()

with col1:
    st.markdown("<div class='pos-container'>", unsafe_allow_html=True)
    st.subheader("Product selection")

    tab_browse, tab_manual, tab_scanner = st.tabs(["Browse", "Barcode (manual)", "Barcode (scanner)"])

    with tab_browse:
        search_term = st.text_input("Search name or barcode", placeholder="Type to filter...")
        if products:
            if search_term:
                q = search_term.lower().strip()
                filtered_products = [
                    p
                    for p in products
                    if q in str(p["productname"]).lower()
                    or q in str(p.get("barcode", "")).lower()
                ]
            else:
                filtered_products = products

            for product in filtered_products[:20]:
                bc = product.get("barcode", "")
                if st.button(
                    f"{product['productname']} — ZMW {float(product['sellingprice']):.2f}",
                    key=f"prod_{product['productid']}",
                    help=f"Barcode: {bc} · Stock: {product['stock']}",
                ):
                    add_to_cart(
                        product["productid"],
                        product["productname"],
                        1,
                        float(product["sellingprice"]),
                    )
                    st.rerun()

            if len(filtered_products) > 20:
                st.info(f"Showing first 20 of {len(filtered_products)} products")
        else:
            st.warning("No products available for sale")

    with tab_manual:
        manual = st.text_input("Enter barcode digits", key="barcode_manual", placeholder="e.g. 6001000000011")
        if st.button("Lookup & add", key="btn_manual_lookup"):
            if manual and manual.strip():
                try_lookup_barcode(manual.strip())
            else:
                st.warning("Enter a barcode first.")

    with tab_scanner:
        st.caption(
            "USB scanners usually behave like a keyboard: click the field, scan, then press Enter or use the button."
        )
        scanner_widget_key = f"barcode_scanner_{st.session_state.barcode_scanner_nonce}"
        scan_val = st.text_input("Scanner input", key=scanner_widget_key, label_visibility="collapsed")
        c1, c2 = st.columns(2)
        if c1.button("Add scanned item", key="btn_scan_add"):
            if scan_val and scan_val.strip():
                try_lookup_barcode(scan_val.strip())
            else:
                st.warning("Scan a barcode into the field first.")
        if c2.button("Clear field", key="btn_scan_clear"):
            st.session_state.barcode_scanner_nonce += 1
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

discount_pct = 0.0

with col2:
    st.markdown("<div class='pos-container'>", unsafe_allow_html=True)
    st.subheader("Shopping Cart")

    cart_items = st.session_state.get("cart", [])

    if cart_items:
        for idx, item in enumerate(cart_items):
            col_a, col_b, col_c = st.columns([3, 1, 1])
            with col_a:
                st.write(f"**{item['product_name']}**")
            with col_b:
                new_qty = st.number_input(
                    "Qty",
                    min_value=1,
                    value=item["quantity"],
                    key=f"qty_{idx}",
                    label_visibility="collapsed",
                )
                if new_qty != item["quantity"]:
                    item["quantity"] = new_qty
                    item["line_total"] = new_qty * item["unit_price"]
                    update_cart_total()
                    st.rerun()
            with col_c:
                if st.button("❌", key=f"remove_{idx}", help="Remove line (cashier needs store PIN)"):
                    request_remove_line(item["product_id"])

            st.write(f"@{item['unit_price']:.2f} = ZMW {item['line_total']:.2f}")
            st.markdown("---")

        col_clear, col_discount = st.columns(2)
        with col_clear:
            if st.button("Clear cart", type="secondary"):
                request_clear_cart()
        with col_discount:
            if str(user_role).lower() == "manager":
                discount_pct = st.number_input(
                    "Discount %",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=5.0,
                )
    else:
        st.info("Cart is empty. Add products from the left.")

    req = st.session_state.pos_removal_request
    if req and str(user_role).lower() == "cashier":
        st.warning("Store authorization required to remove items or clear the cart.")
        pin = st.text_input("Store removal PIN", type="password", key="store_removal_pin")
        b1, b2, b3 = st.columns(3)
        if b1.button("Confirm", type="primary", key="confirm_removal"):
            if StoreSettings.verify_cart_removal_pin(pin or ""):
                if req["action"] == "remove":
                    remove_from_cart(req["product_id"])
                elif req["action"] == "clear":
                    clear_cart()
                st.session_state.pos_removal_request = None
                st.success("Authorized.")
                st.rerun()
            else:
                st.error("Invalid PIN.")
        if b2.button("Cancel", key="cancel_removal"):
            st.session_state.pos_removal_request = None
            st.rerun()
        if b3.button("Continue without removing", key="dismiss_removal"):
            st.session_state.pos_removal_request = None
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='pos-container'>", unsafe_allow_html=True)
    st.subheader("Checkout")

    cart_total = st.session_state.get("cart_total", 0.0)
    discount_amount = cart_total * (discount_pct / 100)
    final_total = cart_total - discount_amount

    st.markdown(
        f"""
    <div class='total-display'>
        Subtotal: ZMW {cart_total:.2f}<br>
        {'Discount: ZMW ' + f'{discount_amount:.2f}' if discount_amount > 0 else ''}<br>
        Total: ZMW {final_total:.2f}
    </div>
    """,
        unsafe_allow_html=True,
    )

    payment_method = st.selectbox("Payment method", ["cash", "card", "mobile_money"])

    if cart_items and final_total > 0:
        if st.button("Complete sale", type="primary", use_container_width=True):
            try:
                sale_id = POSSystem.process_transaction(
                    cart_items=cart_items,
                    total_amount=final_total,
                    processed_by=current_user.user_id,
                    payment_method=payment_method,
                )
                st.session_state.pending_invoice_sale_id = int(sale_id)
                clear_cart()
                st.session_state.pos_removal_request = None
                st.rerun()
            except Exception as exc:
                st.error(f"Error processing sale: {exc}")
    else:
        st.button("Complete sale", type="primary", use_container_width=True, disabled=True)

    st.markdown("---")
    if st.button("New transaction", use_container_width=True):
        clear_cart()
        st.session_state.pos_removal_request = None
        st.rerun()

    st.markdown("---")
    st.markdown(f"**Staff:** {current_user.full_name}")
    st.markdown(f"**Role:** {user_role.title()}")

    st.markdown("</div>", unsafe_allow_html=True)

if cart_items:
    st.markdown("---")
    st.markdown(f"**Cart summary:** {len(cart_items)} items | Total: ZMW {final_total:.2f}")
