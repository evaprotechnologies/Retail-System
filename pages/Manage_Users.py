import streamlit as st
import pandas as pd

from models.admin import StaffAdmin
from models.navigation import render_sidebar
from models.store_settings import CART_REMOVAL_PIN_KEY, StoreSettings
from models.users import User

st.set_page_config(page_title="Manage Users", layout="wide", initial_sidebar_state="expanded")
User.check_login(["manager"], redirect_page="pages/Manage_Users.py")
render_sidebar()

st.title("Manage Users & Cashiers")
st.caption("Add staff, reset passwords, review sales, and configure the store cart-removal PIN.")

tab_staff, tab_pass, tab_pin = st.tabs(["Staff accounts", "Password reset", "Store removal PIN"])

with tab_staff:
    st.subheader("Add cashier or manager")
    with st.form("add_user"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        fn = st.text_input("Full name")
        role = st.selectbox("Role", ["cashier", "manager"])
        if st.form_submit_button("Create user", type="primary"):
            if u and p and fn:
                try:
                    StaffAdmin.add_user(u.strip(), p, fn.strip(), role)
                    st.success("User created.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not create user: {exc}")
            else:
                st.warning("Fill all fields.")

    st.divider()
    st.subheader("All users")
    users = StaffAdmin.list_users()
    if users:
        st.dataframe(pd.DataFrame([dict(r) for r in users]), use_container_width=True, hide_index=True)
    else:
        st.info("No users found.")

    st.divider()
    st.subheader("Cashier profiles & sales")
    cashiers = StaffAdmin.list_cashiers()
    if not cashiers:
        st.info("No cashiers in the system.")
    else:
        for c in cashiers:
            cid = c["userid"]
            label = f"{c['fullname']} ({c['username']}) — active: {c['isactive']}"
            with st.expander(label):
                sales = StaffAdmin.get_cashier_sales(cid)
                if not sales:
                    st.caption("No sales yet.")
                else:
                    sdf = pd.DataFrame([dict(s) for s in sales])
                    st.dataframe(sdf, use_container_width=True, hide_index=True)
                    sale_pick = st.selectbox(
                        "View line items for sale",
                        [int(s["saleid"]) for s in sales],
                        format_func=lambda x: f"Sale #{x}",
                        key=f"sale_pick_{cid}",
                    )
                    if sale_pick:
                        lines = StaffAdmin.get_sale_details(sale_pick)
                        st.dataframe(pd.DataFrame([dict(l) for l in lines]), use_container_width=True, hide_index=True)

                col_a, col_b = st.columns(2)
                if col_a.button("Deactivate", key=f"deact_{cid}"):
                    StaffAdmin.set_user_active(cid, False)
                    st.rerun()
                if col_b.button("Activate", key=f"act_{cid}"):
                    StaffAdmin.set_user_active(cid, True)
                    st.rerun()

with tab_pass:
    st.subheader("Reset staff password")
    st.caption("Managers can set a new login password for any cashier or manager account.")
    users = StaffAdmin.list_users()
    if not users:
        st.info("No users.")
    else:
        urows = {u["userid"]: u for u in users}
        uid = st.selectbox(
            "User",
            list(urows.keys()),
            format_func=lambda i: f"{urows[i]['username']} — {urows[i]['fullname']} ({urows[i]['role']})",
        )
        np = st.text_input("New password", type="password", key="reset_pw1")
        np2 = st.text_input("Confirm new password", type="password", key="reset_pw2")
        if st.button("Update password", type="primary"):
            if not np or np != np2:
                st.error("Passwords must match and cannot be empty.")
            else:
                try:
                    StaffAdmin.update_user_password(int(uid), np)
                    st.success("Password updated.")
                except Exception as exc:
                    st.error(str(exc))

with tab_pin:
    st.subheader("Cart removal PIN")
    st.caption(
        "Cashiers need this PIN to remove a line item or clear the cart. "
        "It is separate from any user login password."
    )
    current = StoreSettings.get_value(CART_REMOVAL_PIN_KEY) or ""
    st.text_input("Current PIN (masked)", value="••••••" if current else "(not set)", disabled=True)
    np = st.text_input("New store PIN", type="password")
    np2 = st.text_input("Confirm new PIN", type="password")
    if st.button("Update store PIN", type="primary"):
        if np and np == np2:
            StoreSettings.update_cart_removal_pin(np)
            st.success("Store removal PIN updated.")
        else:
            st.error("PINs must match and cannot be empty.")
