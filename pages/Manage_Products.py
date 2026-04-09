import streamlit as st
import pandas as pd

from models.inventory import POSSystem
from models.navigation import render_sidebar
from models.users import User

st.set_page_config(page_title="Manage Products", layout="wide", initial_sidebar_state="expanded")
render_sidebar()
User.check_login(["manager"])

st.title("📦 Product Management")

tab1, tab2, tab3 = st.tabs(["➕ Add Product", "✏️ Update Price", "❌ Delete Product"])

with tab1:
    st.subheader("Add New Product")
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Product name")
        new_cat = st.text_input("Category", placeholder="e.g. Groceries")
        new_barcode = st.text_input("Barcode (unique)", placeholder="e.g. 6001000000999")
        new_price = st.number_input("Selling price (ZMW)", min_value=1.0)
    with col2:
        new_stock = st.number_input("Initial stock quantity", min_value=0, step=1)
        suppliers = POSSystem.get_suppliers()
        sup_dict = {s["suppliername"]: s["supplierid"] for s in suppliers}
        selected_sup = st.selectbox("Assign supplier", list(sup_dict.keys()) if sup_dict else ["None"])

    if st.button("Save product", type="primary"):
        if new_name and new_cat and new_barcode and selected_sup != "None":
            supplier_id = sup_dict.get(selected_sup)
            try:
                POSSystem.add_product(new_name.strip(), new_cat.strip(), new_price, supplier_id, new_stock, new_barcode.strip())
                st.success(f"Added '{new_name}'!")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not save product: {exc}")
        elif not new_name:
            st.error("Please enter a product name")
        elif not new_cat:
            st.error("Please enter a category")
        elif not new_barcode:
            st.error("Please enter a unique barcode")
        else:
            st.error("Please select a supplier")

with tab2:
    st.subheader("Update Product Pricing")
    prods = POSSystem.get_products()
    if prods:

        def _label(pid):
            p = next(x for x in prods if x["productid"] == pid)
            return f"{p['productname']} ({p['barcode']})"

        pid = st.selectbox("Select product", [p["productid"] for p in prods], format_func=_label)
        row = next(p for p in prods if p["productid"] == pid)
        current_price = float(row["sellingprice"])

        new_price = st.number_input("New price (ZMW)", value=current_price, min_value=1.0)
        if st.button("Update price"):
            POSSystem.update_price(pid, new_price)
            st.success("Price updated successfully!")
            st.rerun()
    else:
        st.info("No products found to update.")

with tab3:
    st.subheader("Remove a Product")
    st.warning("⚠️ Deleting a product will also remove its stock records.")
    prods = POSSystem.get_products()
    if prods:

        def _label_del(pid):
            p = next(x for x in prods if x["productid"] == pid)
            return f"{p['productname']} ({p['barcode']})"

        pid_del = st.selectbox("Select product to delete", [p["productid"] for p in prods], format_func=_label_del, key="del_box")
        if st.button("Delete product", type="primary"):
            POSSystem.delete_product(pid_del)
            st.success("Product deleted.")
            st.rerun()
    else:
        st.info("No products found to delete.")
