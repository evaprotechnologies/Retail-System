import streamlit as st
import pandas as pd
from models.users import User
from models.inventory import POSSystem

User.check_login(["manager"])
st.set_page_config(page_title="Manage Products", layout="wide")
st.title("📦 Product Management")

# Create 3 Tabs for full CRUD
tab1, tab2, tab3 = st.tabs(["➕ Add Product", "✏️ Update Price", "❌ Delete Product"])

# --- TAB 1: CREATE ---
with tab1:
    st.subheader("Add New Product")
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Product Name")
        new_price = st.number_input("Selling Price (ZMW)", min_value=1.0)
    with col2:
        new_stock = st.number_input("Initial Stock Quantity", min_value=0, step=1)
        suppliers = POSSystem.get_suppliers()
        sup_dict = {s['suppliername']: s['supplierid'] for s in suppliers}
        selected_sup = st.selectbox("Assign Supplier", list(sup_dict.keys()) if sup_dict else ["None"])

    if st.button("Save Product", type="primary"):
        if new_name and selected_sup != "None":
            supplier_id = sup_dict.get(selected_sup)
            POSSystem.add_product(new_name, new_price, supplier_id, new_stock)
            st.success(f"Added '{new_name}'!")
            st.rerun()
        elif not new_name:
            st.error("Please enter a product name")
        else:
            st.error("Please select a supplier")

# --- TAB 2: UPDATE ---
with tab2:
    st.subheader("Update Product Pricing")
    prods = POSSystem.get_products()
    if prods:
        prod_dict = {p['productname']: p for p in prods}
        sel_prod = st.selectbox("Select Product to Update", list(prod_dict.keys()))
        current_price = float(prod_dict[sel_prod]['sellingprice'])

        new_price = st.number_input("New Price (ZMW)", value=current_price, min_value=1.0)
        if st.button("Update Price"):
            POSSystem.update_price(prod_dict[sel_prod]['productid'], new_price)
            st.success("Price updated successfully!")
            st.rerun()
    else:
        st.info("No products found to update.")

# --- TAB 3: DELETE ---
with tab3:
    st.subheader("Remove a Product")
    st.warning("⚠️ Deleting a product will also remove its stock records.")
    prods = POSSystem.get_products()
    if prods:
        prod_dict = {p['productname']: p for p in prods}
        del_prod = st.selectbox("Select Product to Delete", list(prod_dict.keys()), key="del_box")
        if st.button("Delete Product", type="primary"):
            POSSystem.delete_product(prod_dict[del_prod]['productid'])
            st.success(f"{del_prod} deleted.")
            st.rerun()
    else:
        st.info("No products found to delete.")