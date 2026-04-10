import streamlit as st
import pandas as pd

from models.inventory import POSSystem
from models.navigation import render_sidebar
from models.ui_theme import render_page_heading
from models.users import User

st.set_page_config(
    page_title="Sales Analytics",
    page_icon=":material/monitoring:",
    layout="wide",
    initial_sidebar_state="expanded",
)
User.check_login(["manager"], redirect_page="pages/Sales_Analytics.py")
render_sidebar()

render_page_heading("Sales analytics", "Daily revenue, volumes, and transaction counts.")

sales_data = POSSystem.get_sales_summary()

if not sales_data:
    st.info("No sales data available yet. Go to the Point of Sale to make some transactions!")
else:
    df = pd.DataFrame([dict(row) for row in sales_data])

    st.subheader("Key Performance Indicators (Overall)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"ZMW {df['dailyrevenue'].sum():,.2f}")
    col2.metric("Total Items Sold", int(df["totalitemssold"].sum()))
    col3.metric("Total Transactions", int(df["totalinvoices"].sum()))

    st.divider()

    st.subheader("Daily Sales Ledger")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Revenue Trend")
    st.bar_chart(data=df, x="transactiondate", y="dailyrevenue", color="#2563eb")
