import streamlit as st

from models.users import User

st.set_page_config(page_title="Retail System Gateway", page_icon="🔒", layout="centered", initial_sidebar_state="collapsed")

# Initialize session state
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = st.session_state.current_user is not None

if not st.session_state.logged_in or st.session_state.current_user is None:
    # Professional login design
    st.markdown("""
    <style>
        .login-container {
            max-width: 450px;
            margin: 0 auto;
            padding: 2.5rem;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            color: white;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .stTextInput > div > div > input {
            background-color: rgba(255,255,255,0.9);
            border: none;
            border-radius: 8px;
            padding: 0.75rem;
            font-size: 1rem;
        }
        .stTextInput > div > div > input:focus {
            box-shadow: 0 0 0 2px rgba(255,255,255,0.8);
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.title("Retail Management System")
        st.markdown("### Employee Portal")
        st.markdown("---")

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True, type="primary")

            if submit:
                if username and password:
                    user = User.authenticate(username, password)
                    if user:
                        user.persist_to_session()
                        st.success(f"Welcome back, {user.full_name}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.warning("Please enter both username and password")

        st.markdown("<div style='margin-top: 2rem; font-size: 0.85em; opacity: 0.8;'>", unsafe_allow_html=True)
        st.markdown("**Test Accounts:**")
        st.markdown("- Cashier: cashier1 / cashier123")
        st.markdown("- Manager: manager1 / manager123")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
else:
    from models.navigation import render_sidebar

    render_sidebar()

    # Get current user info
    current_user = st.session_state.current_user
    user_role = current_user.role.title() if current_user else "Unknown"

    # Enhanced dashboard design
    st.markdown(f"""
    <style>
        .dashboard-header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 2rem;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        .role-badge {{
            background: {'#28a745' if user_role == 'Manager' else '#007bff'};
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            display: inline-block;
            font-size: 0.9em;
            font-weight: bold;
            margin-bottom: 1rem;
        }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='dashboard-header'>
        <div class='role-badge'>{user_role}</div>
        <h1>System Dashboard</h1>
        <p>Welcome back, {current_user.full_name if current_user else 'User'}!</p>
    </div>
    """, unsafe_allow_html=True)

    st.success("Authentication verified successfully")

    # Role-based navigation
    if user_role.lower() == "cashier":
        # Cashier navigation
        st.markdown("### Available Features")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div style='background: #f8f9fa; padding: 2rem; border-radius: 10px; border-left: 4px solid #28a745; text-align: center;'>
                <h4>Point of Sale</h4>
                <p>Process customer transactions</p>
                <p style='color: #666; font-size: 0.9em;'>Your main workstation</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div style='background: #e9ecef; padding: 2rem; border-radius: 10px; border-left: 4px solid #6c757d; text-align: center; opacity: 0.6;'>
                <h4>Management Tools</h4>
                <p>Access restricted to managers</p>
                <p style='color: #666; font-size: 0.9em;'>Contact manager for access</p>
            </div>
            """, unsafe_allow_html=True)

    else:
        # Manager navigation
        st.markdown("### System Overview")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
            <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #28a745; text-align: center;'>
                <h5>Dashboard</h5>
                <p>Inventory & analytics overview</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #007bff; text-align: center;'>
                <h5>Products</h5>
                <p>Manage catalog & pricing</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #ffc107; text-align: center;'>
                <h5>Point of Sale</h5>
                <p>Process transactions</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown("""
            <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #6f42c1; text-align: center;'>
                <h5>Store Settings</h5>
                <p>Manage users & suppliers</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Use the sidebar to open your role-based menu.**")