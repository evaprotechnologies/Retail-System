import streamlit as st
import pandas as pd

from models.inventory import POSSystem
from models.navigation import render_sidebar
from models.users import User

st.set_page_config(page_title="Dashboard", layout="wide", initial_sidebar_state="expanded")
User.check_login(["manager"], redirect_page="pages/Dashboard.py")
render_sidebar()

st.title("📊 Inventory Dashboard")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Low Stock Alerts")
    low_stock = POSSystem.get_low_stock()
    if low_stock:
        st.error("Action Required: Restock immediately.")
        st.dataframe(pd.DataFrame(low_stock), use_container_width=True)
    else:
        st.success("Inventory levels are healthy.")

with col2:
    st.subheader("Full Product Catalog")
    catalog = POSSystem.get_full_catalog()
    st.dataframe(pd.DataFrame(catalog), use_container_width=True)
