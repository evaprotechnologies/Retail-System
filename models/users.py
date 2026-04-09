import streamlit as st

from models.database import DatabaseConnection

db = DatabaseConnection()


class User:
    """Base class for all system users."""

    def __init__(self, user_id, username, full_name, role):
        self.user_id = user_id
        self.username = username
        self.full_name = full_name
        self.role = role

    @staticmethod
    def authenticate(username, password):
        """Authenticates and returns a Manager or Cashier object."""
        query = """
            SELECT UserID, Username, FullName, Role
            FROM Users
            WHERE Username = %s AND Password = %s AND IsActive = TRUE
        """
        user_data = db.fetch_one(query, (username, password))
        if not user_data:
            return None

        db.execute_query(
            "UPDATE Users SET LastLogin = CURRENT_TIMESTAMP WHERE UserID = %s",
            (user_data["userid"],),
        )

        role = str(user_data["role"]).lower()
        if role == "manager":
            return Manager(user_data["userid"], user_data["username"], user_data["fullname"])
        if role == "cashier":
            return Cashier(user_data["userid"], user_data["username"], user_data["fullname"])
        return None

    @staticmethod
    def check_login(required_roles=None):
        """Protect pages by enforcing login and optional role checks."""
        user = st.session_state.get("current_user")
        if user is None:
            st.warning("Access Denied. Please log in from the Home page first.")
            st.stop()

        if required_roles:
            allowed = {role.lower() for role in required_roles}
            if str(user.role).lower() not in allowed:
                st.error("Access Denied. You do not have permission to view this page.")
                st.stop()

    def to_session_dict(self):
        return {
            "userid": self.user_id,
            "username": self.username,
            "fullname": self.full_name,
            "role": self.role,
        }

    def persist_to_session(self):
        """Stores object and compatibility keys in session state."""
        st.session_state.current_user = self
        st.session_state.logged_in = True
        st.session_state.userid = self.user_id
        st.session_state.username = self.username
        st.session_state.fullname = self.full_name
        st.session_state.user_role = self.role


class Manager(User):
    """Elevated privileges for store management."""

    def __init__(self, user_id, username, full_name):
        super().__init__(user_id=user_id, username=username, full_name=full_name, role="manager")

    def authorize_void(self, passcode):
        """Verifies manager override using manager account password."""
        query = "SELECT UserID FROM Users WHERE Role = 'manager' AND Password = %s AND IsActive = TRUE"
        return bool(db.fetch_one(query, (passcode,)))

    def add_staff(self, new_user, new_pass, full_name):
        query = """
            INSERT INTO Users (Username, Password, FullName, Role, IsActive)
            VALUES (%s, %s, %s, 'cashier', TRUE)
        """
        db.execute_query(query, (new_user, new_pass, full_name))


class Cashier(User):
    """Standard privileges for POS operations."""

    def __init__(self, user_id, username, full_name):
        super().__init__(user_id=user_id, username=username, full_name=full_name, role="cashier")

