"""Role-based sidebar navigation (requires client.showSidebarNavigation = false)."""

import streamlit as st

from models.ui_theme import inject_global_styles


def render_sidebar():
    """Show navigation links allowed for the current user's role."""
    user = st.session_state.get("current_user")
    if user is None:
        return

    inject_global_styles()

    role = str(user.role).lower()
    with st.sidebar:
        st.markdown(
            """
<div style="margin-bottom:0.75rem;">
  <div style="font-weight:700;font-size:1.05rem;color:#f8fafc;letter-spacing:-0.02em;">Retail OS</div>
  <div style="font-size:0.78rem;color:#94a3b8;margin-top:0.15rem;">Store operations</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.caption(f"{user.full_name} · {role.title()}")

        st.page_link("app.py", label="Home", icon=":material/home:")

        if role == "cashier":
            st.page_link("pages/Point_of_Sale.py", label="Point of Sale", icon=":material/point_of_sale:")
            st.page_link("pages/Cashier_Handover.py", label="My Sales & Handover", icon=":material/receipt_long:")
        else:
            st.page_link("pages/Dashboard.py", label="Dashboard", icon=":material/space_dashboard:")
            st.page_link("pages/Manage_Suppliers.py", label="Manage Suppliers", icon=":material/local_shipping:")
            st.page_link("pages/Manage_Products.py", label="Manage Products", icon=":material/inventory_2:")
            st.page_link("pages/Point_of_Sale.py", label="Point of Sale", icon=":material/point_of_sale:")
            st.page_link("pages/Sales_Analytics.py", label="Sales Analytics", icon=":material/monitoring:")
            st.page_link("pages/Invoices_Audit.py", label="Invoices & audit", icon=":material/fact_check:")
            st.page_link("pages/Manage_Users.py", label="Manage Users", icon=":material/manage_accounts:")

        st.divider()
        if st.button("Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
