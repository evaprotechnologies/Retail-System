import streamlit as st

from models.ui_theme import (
    inject_global_styles,
    render_home_hero,
    render_login_shell_end,
    render_login_shell_start,
)
from models.users import User

st.set_page_config(
    page_title="Retail System Gateway",
    page_icon=":material/store:",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Initialize session state
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = st.session_state.current_user is not None
if "intended_page" not in st.session_state:
    st.session_state.intended_page = None

if not st.session_state.logged_in or st.session_state.current_user is None:
    inject_global_styles()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        render_login_shell_start()

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Sign in", use_container_width=True, type="primary")

            if submit:
                if username and password:
                    user = User.authenticate(username, password)
                    if user:
                        user.persist_to_session()
                        intended_page = st.session_state.get("intended_page")
                        if intended_page:
                            st.session_state.intended_page = None
                            st.success(f"Welcome back, {user.full_name}! Returning to your previous page...")
                            st.switch_page(intended_page)
                        else:
                            st.success(f"Welcome back, {user.full_name}!")
                            st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.warning("Please enter both username and password")

        st.markdown(
            "<p style='color:#64748b;font-size:0.85rem;margin-top:1.25rem;text-align:center;'>"
            "<strong>Demo access</strong><br/>Cashier: cashier1 / cashier123 · Manager: manager1 / manager123</p>",
            unsafe_allow_html=True,
        )

        render_login_shell_end()
else:
    from models.navigation import render_sidebar

    render_sidebar()

    current_user = st.session_state.current_user
    user_role = current_user.role.title() if current_user else "Unknown"

    render_home_hero(user_role, current_user.full_name if current_user else "User")

    st.success("Authentication verified successfully")

    if user_role.lower() == "cashier":
        st.markdown("### Your workspace")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                """
<div class="rs-feature-card" style="--rs-accent:#059669;">
  <h4>Point of Sale</h4>
  <p>Process customer transactions and issue receipts.</p>
  <p style="font-size:0.8rem;margin-top:0.5rem;">Primary cashier workflow</p>
</div>
""",
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                """
<div class="rs-feature-card muted" style="--rs-accent:#64748b;">
  <h4>Management tools</h4>
  <p>Restricted to manager accounts.</p>
  <p style="font-size:0.8rem;margin-top:0.5rem;">Contact a supervisor for access</p>
</div>
""",
                unsafe_allow_html=True,
            )

    else:
        st.markdown("### Quick orientation")
        col1, col2, col3, col4 = st.columns(4)

        blocks = [
            ("Dashboard", "Inventory & stock overview", "#059669"),
            ("Products", "Catalog & pricing", "#2563eb"),
            ("Point of Sale", "Checkout & invoices", "#d97706"),
            ("Users & suppliers", "Staff & vendors", "#7c3aed"),
        ]
        for i, (title, desc, color) in enumerate(blocks):
            with [col1, col2, col3, col4][i]:
                st.markdown(
                    f"""
<div class="rs-feature-card" style="--rs-accent:{color};">
  <h5>{title}</h5>
  <p>{desc}</p>
</div>
""",
                    unsafe_allow_html=True,
                )

    st.divider()
    st.caption("Use the sidebar to open your role-based menu.")
