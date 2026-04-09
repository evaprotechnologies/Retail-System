import streamlit as st
import pandas as pd

from models.inventory import POSSystem
from models.invoice import InvoiceService
from models.navigation import render_sidebar
from models.users import User

st.set_page_config(page_title="My Sales & Handover", layout="wide", initial_sidebar_state="expanded")
render_sidebar()
User.check_login(["cashier"])

user = st.session_state.current_user
st.title("My Sales & Handover")
st.caption("Review your transactions for shift handover and reconciliation.")

sales = POSSystem.get_sales_for_user(user.user_id)

if not sales:
    st.info("No sales recorded for your account yet.")
else:
    df = pd.DataFrame([dict(row) for row in sales])
    st.subheader("Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Transactions", len(df))
    c2.metric("Total ZMW", f"{df['totalamount'].sum():,.2f}")
    c3.metric("Avg ticket", f"{df['totalamount'].mean():,.2f}")

    st.divider()
    st.subheader("Transaction list")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Line items & customer invoice")
    sale_ids = [int(row["saleid"]) for row in sales]
    pick = st.selectbox("Sale ID", sale_ids, format_func=lambda x: f"Sale #{x}")
    if pick:
        try:
            pdf_bytes = InvoiceService.get_pdf_for_user(int(pick), user)
            st.download_button(
                "Download customer invoice (PDF)",
                data=pdf_bytes,
                file_name=f"invoice_{pick}.pdf",
                mime="application/pdf",
                type="primary",
                key=f"handover_dl_{pick}",
            )
            with st.expander("View receipt (on screen)", expanded=False):
                st.text(InvoiceService.format_receipt_text(int(pick)))
        except Exception as exc:
            st.error(f"Could not load invoice: {exc}")

        lines = POSSystem.get_sale_line_items(pick)
        if lines:
            st.dataframe(pd.DataFrame([dict(r) for r in lines]), use_container_width=True, hide_index=True)
        else:
            st.warning("No line items found for this sale.")
