import urllib.parse

import pandas as pd
import streamlit as st

from models.inventory import POSSystem
from models.navigation import render_sidebar
from models.store_settings import StoreSettings
from models.supplier_logistics import (
    RESTOCK_BODY_KEY,
    RESTOCK_SUBJECT_KEY,
    STORE_DISPLAY_KEY,
    SupplierLogistics,
)
from models.users import User

st.set_page_config(page_title="Manage Suppliers", layout="wide", initial_sidebar_state="expanded")
User.check_login(["manager"], redirect_page="pages/Manage_Suppliers.py")
render_sidebar()

st.title("Supplier management")
st.caption(
    "Directory, goods-in delivery notes (updates stock), supplier invoices (pending / paid), "
    "and low-stock restock emails with editable templates."
)

try:
    _probe = SupplierLogistics.list_deliveries(1)
except Exception as exc:
    err = str(exc).lower()
    if "supplierdeliveries" in err or "does not exist" in err or "undefinedtable" in err:
        st.error(
            "Supplier logistics tables are not installed. Run **`migration_supplier_logistics.sql`** "
            "on your database (e.g. with `psql`), then refresh this page."
        )
        st.stop()
    raise

tab_dir, tab_deliveries, tab_invoices, tab_restock = st.tabs(
    ["Supplier directory", "Delivery notes (goods-in)", "Supplier invoices (AP)", "Restock email & templates"]
)

# ----- Directory -----
with tab_dir:
    st.subheader("Browse, add, edit")
    d1, d2, d3 = st.tabs(["All suppliers", "Add supplier", "Edit / delete"])

    with d1:
        rows = POSSystem.get_suppliers_detailed()
        if rows:
            st.dataframe(pd.DataFrame([dict(r) for r in rows]), use_container_width=True, hide_index=True)
        else:
            st.info("No suppliers yet. Use **Add supplier**.")

    with d2:
        with st.form("add_supplier"):
            n = st.text_input("Supplier name *")
            c = st.text_input("Contact person")
            ph = st.text_input("Phone")
            em = st.text_input("Email")
            if st.form_submit_button("Save supplier", type="primary"):
                if n and n.strip():
                    try:
                        sid = POSSystem.add_supplier(n, c, ph, em)
                        st.success(f"Supplier #{sid} created.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not save: {exc}")
                else:
                    st.warning("Supplier name is required.")

    with d3:
        rows = POSSystem.get_suppliers_detailed()
        if not rows:
            st.info("No suppliers to edit.")
        else:
            by_id = {r["supplierid"]: r for r in rows}
            sid = st.selectbox(
                "Select supplier",
                list(by_id.keys()),
                format_func=lambda i: f"{by_id[i]['suppliername']} (ID {i})",
            )
            r = by_id[sid]
            with st.form("edit_supplier"):
                n2 = st.text_input("Supplier name", value=r["suppliername"])
                c2 = st.text_input("Contact person", value=r.get("contactperson") or "")
                ph2 = st.text_input("Phone", value=r.get("phonenumber") or "")
                em2 = st.text_input("Email", value=r.get("email") or "")
                save = st.form_submit_button("Save changes", type="primary")
                if save:
                    try:
                        POSSystem.update_supplier(sid, n2, c2, ph2, em2)
                        st.success("Supplier updated.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

            st.divider()
            st.subheader("Products from this supplier")
            prods = POSSystem.get_supplier_products(sid)
            if prods:
                st.dataframe(pd.DataFrame([dict(p) for p in prods]), use_container_width=True, hide_index=True)
            else:
                st.caption("No products linked.")

            st.divider()
            if st.button("Delete supplier", type="secondary"):
                try:
                    POSSystem.delete_supplier(sid)
                    st.success("Supplier removed.")
                    st.rerun()
                except ValueError as ve:
                    st.error(str(ve))
                except Exception as exc:
                    st.error(str(exc))

# ----- Delivery notes -----
with tab_deliveries:
    st.markdown(
        "Record **stock deliveries** (delivery notes). Lines **increase on-hand stock** immediately. "
        "Use **Supplier invoices** for amounts owed / paid."
    )
    deliveries = SupplierLogistics.list_deliveries(250)
    if deliveries:
        st.dataframe(pd.DataFrame([dict(r) for r in deliveries]), use_container_width=True, hide_index=True)
        expand = st.selectbox(
            "View lines for delivery",
            [d["deliveryid"] for d in deliveries],
            format_func=lambda x: f"Delivery #{x}",
        )
        if expand:
            lines = SupplierLogistics.get_delivery_lines(int(expand))
            if lines:
                st.dataframe(pd.DataFrame([dict(x) for x in lines]), use_container_width=True, hide_index=True)
    else:
        st.caption("No delivery notes recorded yet.")

    st.divider()
    st.subheader("New delivery note")
    sups = POSSystem.get_suppliers_detailed()
    if not sups:
        st.warning("Create a supplier first.")
    else:
        s_map = {r["supplierid"]: r for r in sups}
        dsid = st.selectbox(
            "Supplier",
            list(s_map.keys()),
            format_func=lambda i: s_map[i]["suppliername"],
            key="new_del_supplier",
        )
        if "delivery_lines" not in st.session_state:
            st.session_state.delivery_lines = []
        if "last_del_supplier" not in st.session_state:
            st.session_state.last_del_supplier = None
        if st.session_state.last_del_supplier != dsid:
            st.session_state.delivery_lines = []
            st.session_state.last_del_supplier = dsid

        ddate = st.date_input("Delivery date", key="del_date")
        ref = st.text_input("Reference / GRN (optional)", key="del_ref")
        dnotes = st.text_area("Notes (optional)", key="del_notes")

        prods = POSSystem.get_supplier_products(dsid)
        if prods:
            p_map = {p["productid"]: p for p in prods}
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            with c1:
                pid_pick = st.selectbox(
                    "Product",
                    list(p_map.keys()),
                    format_func=lambda i: p_map[i]["productname"],
                    key="del_prod_pick",
                )
            with c2:
                qty_in = st.number_input("Qty", min_value=1, value=1, key="del_qty")
            with c3:
                cost_in = st.number_input("Unit cost (optional)", min_value=0.0, value=0.0, step=0.01, key="del_cost")
            with c4:
                st.write("")
                st.write("")
                if st.button("Add line"):
                    line = {
                        "product_id": int(pid_pick),
                        "quantity_received": int(qty_in),
                        "unit_cost": float(cost_in) if cost_in > 0 else None,
                    }
                    st.session_state.delivery_lines.append(line)
                    st.rerun()
        else:
            st.warning("No products linked to this supplier — add products in **Manage Products** first.")

        if st.session_state.delivery_lines:
            st.markdown("**Lines to post**")
            st.dataframe(pd.DataFrame(st.session_state.delivery_lines), use_container_width=True, hide_index=True)
            if st.button("Clear lines"):
                st.session_state.delivery_lines = []
                st.rerun()

        mgr = st.session_state.current_user
        if st.button("Record delivery & update stock", type="primary"):
            try:
                did = SupplierLogistics.record_delivery(
                    supplier_id=int(dsid),
                    delivery_date=ddate,
                    reference_code=ref,
                    notes=dnotes,
                    created_by=int(mgr.user_id),
                    lines=st.session_state.delivery_lines,
                )
                st.success(f"Delivery #{did} saved; stock updated.")
                st.session_state.delivery_lines = []
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

# ----- Invoices -----
with tab_invoices:
    st.markdown(
        "Track **supplier invoices**: *pending* = unpaid, *paid* = settled. Optional link to a **delivery note**. "
        "This is for **accounts / audit** (supplier billing), not customer receipts."
    )
    inv_all = SupplierLogistics.list_invoices(400)
    if inv_all:
        status_filter = st.multiselect(
            "Filter status",
            ["pending", "paid", "cancelled"],
            default=["pending", "paid", "cancelled"],
        )
        inv_all = [x for x in inv_all if str(x["status"]).lower() in [s.lower() for s in status_filter]]
        if inv_all:
            st.dataframe(pd.DataFrame([dict(r) for r in inv_all]), use_container_width=True, hide_index=True)
        else:
            st.caption("No rows for this filter.")
    else:
        st.caption("No supplier invoices yet.")

    st.divider()
    st.subheader("Register supplier invoice")
    sups = POSSystem.get_suppliers_detailed()
    if sups:
        sm = {r["supplierid"]: r for r in sups}
        inv_sid = st.selectbox(
            "Supplier",
            list(sm.keys()),
            format_func=lambda i: sm[i]["suppliername"],
            key="inv_sup",
        )
        dels = SupplierLogistics.list_deliveries_for_supplier(int(inv_sid))
        del_opts = [None] + [d["deliveryid"] for d in dels]
        del_pick = st.selectbox(
            "Link delivery note (optional)",
            del_opts,
            format_func=lambda x: "— none —" if x is None else f"Delivery #{x}",
        )
        with st.form("new_inv"):
            inv_no = st.text_input("Invoice / document number *")
            inv_dt = st.date_input("Invoice date")
            use_due = st.checkbox("Set due date", value=False)
            due_dt = st.date_input("Due date", disabled=not use_due) if use_due else None
            amt = st.number_input("Amount (ZMW)", min_value=0.0, value=0.0, step=0.01)
            stt = st.selectbox("Status", ["pending", "paid"])
            ninv = st.text_area("Notes")
            if st.form_submit_button("Save invoice"):
                if inv_no.strip() and amt > 0:
                    try:
                        SupplierLogistics.add_invoice(
                            supplier_id=int(inv_sid),
                            invoice_number=inv_no.strip(),
                            invoice_date=inv_dt,
                            due_date=due_dt,
                            amount=amt,
                            status=stt,
                            notes=ninv,
                            delivery_id=int(del_pick) if del_pick else None,
                        )
                        st.success("Invoice saved.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
                else:
                    st.warning("Enter invoice number and a positive amount.")

    st.divider()
    st.subheader("Update invoice status")
    inv2 = SupplierLogistics.list_invoices(400)
    if inv2:
        iid = st.selectbox(
            "Invoice",
            [r["invoiceid"] for r in inv2],
            format_func=lambda i: next(
                f"#{i} — {r['suppliername']} — {r['invoicenumber']} — {r['status']} — ZMW {float(r['amount']):.2f}"
                for r in inv2
                if r["invoiceid"] == i
            ),
        )
        new_st = st.selectbox("New status", ["pending", "paid", "cancelled"], key="inv_newst")
        if st.button("Apply status"):
            try:
                SupplierLogistics.update_invoice_status(int(iid), new_st)
                st.success("Updated.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

# ----- Restock email -----
with tab_restock:
    st.markdown(
        "Templates support placeholders: **`{store_name}`**, **`{supplier_name}`**, **`{items_table}`**. "
        "Generated email opens in your mail client; you can edit before sending."
    )
    t1, t2 = st.tabs(["Edit templates & store name", "Generate for supplier"])

    with t1:
        store_n = st.text_input(
            "Store display name",
            value=StoreSettings.get_value(STORE_DISPLAY_KEY) or "Retail Supermarket",
        )
        subj = st.text_input(
            "Email subject template",
            value=StoreSettings.get_value(RESTOCK_SUBJECT_KEY)
            or "Restock request — {store_name} (low stock)",
        )
        body = st.text_area(
            "Email body template",
            value=StoreSettings.get_value(RESTOCK_BODY_KEY)
            or (
                "Dear {supplier_name},\n\n"
                "Please arrange supply for the following items:\n\n{items_table}\n\n"
                "Regards,\n{store_name}"
            ),
            height=220,
        )
        if st.button("Save templates", type="primary"):
            StoreSettings.upsert_value(STORE_DISPLAY_KEY, store_n.strip())
            StoreSettings.upsert_value(RESTOCK_SUBJECT_KEY, subj.strip())
            StoreSettings.upsert_value(RESTOCK_BODY_KEY, body)
            st.success("Saved.")

    with t2:
        sups = POSSystem.get_suppliers_detailed()
        if not sups:
            st.warning("No suppliers.")
        else:
            sm = {r["supplierid"]: r for r in sups}
            rsid = st.selectbox(
                "Supplier",
                list(sm.keys()),
                format_func=lambda i: sm[i]["suppliername"],
                key="restock_sup",
            )
            if st.button("Generate draft", type="primary"):
                try:
                    sub, bod, em = SupplierLogistics.format_restock_email(int(rsid))
                    st.session_state["restock_payload"] = (sub, bod, em or "")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

            payload = st.session_state.get("restock_payload")
            if payload:
                sub0, bod0, em_to = payload
                st.caption(f"Supplier email on file: `{em_to or '— add email in supplier directory —'}`")
                sub_final = st.text_input("Subject (edit as needed)", value=sub0, key="mail_subj")
                bod_final = st.text_area("Body (edit as needed)", value=bod0, height=260, key="mail_body")
                if em_to:
                    q_sub = urllib.parse.quote(sub_final)
                    q_body = urllib.parse.quote(bod_final)
                    mailto = f"mailto:{urllib.parse.quote(em_to)}?subject={q_sub}&body={q_body}"
                    st.link_button("Open in email app (mailto)", mailto)
                st.download_button(
                    "Download draft as .txt",
                    f"Subject: {sub_final}\n\n{bod_final}",
                    file_name="restock_request_draft.txt",
                    mime="text/plain",
                )
                if st.button("Clear draft"):
                    del st.session_state["restock_payload"]
                    st.rerun()
