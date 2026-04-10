"""Role-based sidebar navigation (requires client.showSidebarNavigation = false)."""

import streamlit as st


def render_sidebar():
    """Show navigation links allowed for the current user's role."""
    user = st.session_state.get("current_user")
    if user is None:
        return

    role = str(user.role).lower()
    with st.sidebar:
        st.markdown("### Retail System")
        st.caption(f"{user.full_name} · {role.title()}")

        st.page_link("app.py", label="Home", icon="🏠")

        if role == "cashier":
            st.page_link("pages/Point_of_Sale.py", label="Point of Sale", icon="🧾")
            st.page_link("pages/Cashier_Handover.py", label="My Sales & Handover", icon="📋")
        else:
            st.page_link("pages/Dashboard.py", label="Dashboard", icon="📊")
            st.page_link("pages/Manage_Suppliers.py", label="Manage Suppliers", icon="🚚")
            st.page_link("pages/Manage_Products.py", label="Manage Products", icon="📦")
            st.page_link("pages/Point_of_Sale.py", label="Point of Sale", icon="🧾")
            st.page_link("pages/Sales_Analytics.py", label="Sales Analytics", icon="📈")
            st.page_link("pages/Invoices_Audit.py", label="Invoices & audit", icon="📄")
            st.page_link("pages/Manage_Users.py", label="Manage Users", icon="👥")

        st.divider()
        if st.button("Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
