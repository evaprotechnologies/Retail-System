import streamlit as st
import pandas as pd

from models.inventory import POSSystem
from models.invoice import InvoiceService
from models.navigation import render_sidebar
from models.users import User

st.set_page_config(page_title="Invoices & audit", layout="wide", initial_sidebar_state="expanded")
render_sidebar()
User.check_login(["manager"])

st.title("Invoices & audit")
st.caption("Every sale has a customer invoice (PDF). Open or download for audits or reprints.")

sales = POSSystem.list_recent_sales(500)
if not sales:
    st.info("No sales in the database yet.")
    st.stop()

df = pd.DataFrame([dict(r) for r in sales])
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Invoice for a transaction")
ids = [int(r["saleid"]) for r in sales]


def _fmt_sale(sid: int):
    row = next(x for x in sales if int(x["saleid"]) == sid)
    sd = row["saledate"]
    return f"#{sid} — {sd} — ZMW {float(row['totalamount']):.2f} — {row.get('cashiername', '')}"


pick = st.selectbox("Select sale", ids, format_func=_fmt_sale)
user = st.session_state.current_user

if pick:
    try:
        pdf_bytes = InvoiceService.get_pdf_for_user(int(pick), user)
        st.download_button(
            "Download invoice (PDF)",
            data=pdf_bytes,
            file_name=f"invoice_{pick}.pdf",
            mime="application/pdf",
            type="primary",
            key=f"audit_dl_{pick}",
        )
        with st.expander("View receipt (on screen)", expanded=True):
            st.text(InvoiceService.format_receipt_text(int(pick)))
        lines = POSSystem.get_sale_line_items(int(pick))
        if lines:
            st.subheader("Line items")
            st.dataframe(pd.DataFrame([dict(x) for x in lines]), use_container_width=True, hide_index=True)
    except PermissionError:
        st.error("Access denied.")
    except Exception as exc:
        st.error(str(exc))
