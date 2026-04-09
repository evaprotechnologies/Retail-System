import streamlit as st
import pandas as pd
from models.users import User
from models.inventory import POSSystem

# Security Check
User.check_login(["manager"])

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("📊 Inventory Dashboard")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Low Stock Alerts")
    low_stock = POSSystem.get_low_stock()
    if low_stock:
        st.error("Action Required: Restock immediately.")
        st.dataframe(pd.DataFrame(low_stock), width='stretch')
    else:
        st.success("Inventory levels are healthy.")

with col2:
    st.subheader("Full Product Catalog")
    catalog = POSSystem.get_full_catalog()
    st.dataframe(pd.DataFrame(catalog), width='stretch')