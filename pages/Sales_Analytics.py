import streamlit as st
import pandas as pd
from models.users import User
from models.inventory import POSSystem

User.check_login(["manager"])
st.set_page_config(page_title="Sales Analytics", layout="wide")
st.title("📈 Sales Analytics & Reports")

# Fetch data from the Advanced SQL View we created
sales_data = POSSystem.get_sales_summary()

if not sales_data:
    st.info("No sales data available yet. Go to the Point of Sale to make some transactions!")
else:
    df = pd.DataFrame([dict(row) for row in sales_data])
    
    # Top KPI Metrics
    st.subheader("Key Performance Indicators (Overall)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"ZMW {df['dailyrevenue'].sum():,.2f}")
    col2.metric("Total Items Sold", int(df['totalitemssold'].sum()))
    col3.metric("Total Transactions", int(df['totalinvoices'].sum()))
    
    st.divider()
    
    # Detailed Table
    st.subheader("Daily Sales Ledger")
    st.dataframe(df, width='stretch', hide_index=True)
    
    # Visual Chart
    st.subheader("Revenue Trend")
    st.bar_chart(data=df, x='transactiondate', y='dailyrevenue', color="#0083B8")