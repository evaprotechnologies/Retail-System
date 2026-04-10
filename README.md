# Retail Inventory & Sales Management System

A Streamlit + PostgreSQL retail platform for grocery-style operations, with **role-based access** (**Manager** / **Cashier**), an **object-oriented** `models/` layer, **supplier CRUD**, **login redirect & resume**, **barcode POS**, **PDF invoices**, and **staff / audit** tools.

---

## Tech Stack

- Python 3.10+
- Streamlit (≥ 1.33 recommended, for `st.page_link` and sidebar config)
- PostgreSQL
- `psycopg2-binary`, `pandas`, `fpdf2` (PDF invoices)

---

## Project Structure

```text
Retail_System_Project/
├── app.py                          # Login gateway + role-aware home
├── .streamlit/
│   └── config.toml                 # Hides default multipage nav (custom sidebar)
├── database_schema.sql             # Current DB schema + compact demo seed
├── rebuild_retail_grocery_db.sql   # Full wipe/rebuild + rich supermarket seed
├── migration_add_barcode_store_settings.sql  # Upgrade old DBs (Barcode + StoreSettings)
├── seed_sample_supplier_logistics.sql        # Optional demo rows for deliveries + supplier invoices
├── requirements.txt
├── README.md
│
├── models/                         # OOP business / data access layer
│   ├── __init__.py
│   ├── database.py                 # DatabaseConnection (env / secrets aware)
│   ├── users.py                    # User, Manager, Cashier + authenticate, check_login
│   ├── inventory.py                # POSSystem (products, sales, catalog, CRUD)
│   ├── invoice.py                  # InvoiceService — PDF + receipt text from Sales
│   ├── admin.py                    # StaffAdmin — user lists, cashier sales drill-down
│   ├── supplier_logistics.py       # Deliveries (goods-in), supplier AP invoices, restock email text
│   ├── store_settings.py           # StoreSettings — cart PIN, email templates, store name
│   └── navigation.py               # Role-based sidebar (st.page_link)
│
├── pages/
│   ├── Dashboard.py                # Manager — low stock + catalog
│   ├── Manage_Suppliers.py         # Manager — supplier CRUD + linked products
│   ├── Manage_Products.py          # Manager — products + barcodes
│   ├── Point_of_Sale.py            # POS — browse / barcode / scanner, cart PIN
│   ├── Sales_Analytics.py          # Manager — daily sales view
│   ├── Manage_Users.py             # Manager — staff, password reset, sales drill-down, store PIN
│   ├── Cashier_Handover.py         # Cashier — own sales + invoice PDF
│   └── Invoices_Audit.py           # Manager — all sales + invoice PDF / audit
```

---

## Features (Current)

### Authentication & navigation

- Login via `User.authenticate()`; session stores `current_user` (`Manager` or `Cashier`) plus legacy keys (`userid`, `user_role`, …).
- **`User.check_login(required_roles, redirect_page="pages/....py")`** on protected pages:
  - If the user is **not logged in**, the app stores **`st.session_state.intended_page`** and calls **`st.switch_page("app.py")`** so they see the login form on the home app.
  - After a **successful login**, `app.py` reads `intended_page` and calls **`st.switch_page`** to **resume the same page** (e.g. return to POS after being sent to login).
  - Wrong role for a page still shows an error and **does not** redirect (by design).
- **Note:** Streamlit **session state** is tied to the browser session. A **new** or **cleared** session cannot recover an in-memory cart from the server; `intended_page` restores **which screen** opens after login, not server-side cart persistence.
- **Custom sidebar** (`models/navigation.py`): `.streamlit/config.toml` hides the default multipage list; each role sees only allowed links + **Logout**.

### Point of Sale

- Product browse with **name or barcode** search.
- **Barcode (manual)** and **Barcode (scanner)** tabs (USB scanners as keyboard wedge).
- **Cart:** quantity edits; **managers** may remove lines / clear cart freely.
- **Cashiers** need the **store removal PIN** (not their login password) to remove a line or clear the cart — configured in **StoreSettings** (`cart_removal_pin`; default in seed scripts).
- **Manager discount %** on subtotal.
- **Checkout** with payment method: `cash`, `card`, `mobile_money`.

### Invoices (customer receipt / audit)

- Each sale is stored in **`Sales`** + **`Sales_Details`**.
- **`InvoiceService`** builds a **PDF** and on-screen receipt text from that data (no duplicate file storage).
- After **Complete sale**, POS shows **Download invoice (PDF)** + preview + dismiss.
- **Cashier:** **My Sales & Handover** — per-transaction PDF and line items.
- **Manager:** **Invoices & audit** — recent sales list, PDF download, preview, lines.

### Manager tools

- **Dashboard** — low stock + full catalog (with barcodes).
- **Manage Suppliers** (multi-tab): **directory** (CRUD, linked products); **Delivery notes (goods-in)** — record deliveries, line items, optional unit costs; **updates stock** on save; history + line view; **Supplier invoices (AP)** — register invoices (*pending* / *paid* / *cancelled*), optional link to a delivery note, status updates; **Restock email** — editable templates (`{store_name}`, `{supplier_name}`, `{items_table}`) in `StoreSettings`, generate draft from **low stock** per supplier, `mailto:` + `.txt` download (no SMTP; manager edits and sends from their email client).
- **Manage Products** — add/update/delete; **unique barcode** per SKU; supplier assignment uses live supplier list.
- **Sales Analytics** — KPIs from `View_DailySales_Summary`.
- **Manage Users** — create cashiers/managers; **Password reset** tab to set a new login password for any user; **Activate / Deactivate** per cashier; per-cashier **sales** + **Sales_Details**; **Store removal PIN** tab (cart line removal — not the same as login passwords).
- **Invoices & audit** — browse sales and download PDF receipts.

### Database (current schema)

| Table / object | Purpose |
|----------------|---------|
| **Users** | Staff accounts, roles `cashier` \| `manager`, `IsActive`, `LastLogin` |
| **StoreSettings** | Key/value: `cart_removal_pin`, `store_display_name`, `restock_email_*` templates |
| **SupplierDeliveries** / **SupplierDeliveryLines** | Goods-in / delivery notes; lines increase **Stock** |
| **SupplierInvoices** | Supplier billing: amount, status (`pending`/`paid`/`cancelled`), optional **DeliveryID** link |
| **Suppliers** | Supplier master data |
| **Products** | SKU, **Barcode** (unique), category, price, optional `LastPriceUpdatedBy` |
| **Stock** | Quantity per product, reorder level |
| **Sales** | Header: total, `ProcessedBy`, `PaymentMethod`, timestamp |
| **Sales_Details** | Line items; trigger reduces **Stock** |
| **Views** | `View_DailySales_Summary`, `View_LowStock_Alerts`, `View_Product_Catalog` (includes **Barcode**) |
| **Triggers** | Post-insert stock deduction (`GREATEST` clamp); price update timestamp on `Products` |

Full definitions: **`database_schema.sql`** (compact seed) or **`rebuild_retail_grocery_db.sql`** (full grocery dataset).

---

## Architecture

- **UI:** `app.py` + `pages/*` — Streamlit only; no raw SQL in pages where replaced by `models/`.
- **Domain / data access:** `models/*` — `DatabaseConnection`, `POSSystem`, `InvoiceService`, `StaffAdmin`, etc.
- **PostgreSQL:** single source of truth for sales; invoices generated on demand for audit and customer copy.

---

## Setup (Windows / PowerShell)

### 1) Project folder

```powershell
cd "C:\Users\Apollo IT\Documents\DevHub\Retail_System_Project"
```

### 2) Virtual environment (recommended)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3) Create database

```sql
CREATE DATABASE retailsystemdb;
```

### 4) Load schema (pick one)

- **Compact demo (matches `database_schema.sql`):**

  ```powershell
  & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d retailsystemdb -f database_schema.sql
  ```

- **Full supermarket rebuild (drops existing tables in that DB):**

  ```powershell
  & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d retailsystemdb -f rebuild_retail_grocery_db.sql
  ```

- **Existing database missing barcode / StoreSettings:**

  ```powershell
  $env:PGPASSWORD="your_password"
  & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d retailsystemdb -f migration_add_barcode_store_settings.sql
  ```

- **Add supplier logistics (deliveries + supplier invoices + restock template keys):**

  ```powershell
  & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d retailsystemdb -f migration_supplier_logistics.sql
  ```

- **Optional sample rows** for delivery notes and supplier AP invoices (skips if `GRN-DEMO-001` / `GRN-DEMO-002` already exist):

  ```powershell
  & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d retailsystemdb -f seed_sample_supplier_logistics.sql
  ```

  Fresh loads from **`database_schema.sql`** or **`rebuild_retail_grocery_db.sql`** already include built-in samples; use **`seed_sample_supplier_logistics.sql`** mainly on older databases that have logistics tables but no demo data.

Use your real `psql` path and credentials if they differ.

### 5) Configure DB connection for the app

Resolved in `models/database.py`: Streamlit **secrets** (if present), else **environment variables**, else defaults.

```powershell
$env:DB_HOST="localhost"
$env:DB_NAME="retailsystemdb"
$env:DB_USER="postgres"
$env:DB_PASSWORD="your_password"
$env:DB_PORT="5432"
```

Optional: `.streamlit/secrets.toml` with the same keys.

### 6) Run Streamlit

```powershell
streamlit run app.py
```

---

## Default test accounts (`database_schema.sql` compact seed)

- **Cashier:** `cashier1` / `cashier123`
- **Manager:** `manager1` / `manager123`

**Store cart-removal PIN (seed):** `882244` — change under **Manage Users → Store removal PIN** (managers only).

`rebuild_retail_grocery_db.sql` adds more users (e.g. `manager2`, `cashier2`, `cashier3`); see that file for its seed list.

---

## Security notes (development vs production)

- Sample passwords are **plain text** for coursework/demo only.
- **Cart removal PIN** is separate from login passwords; still protect it in production (rotation, access control).
- For production: hash passwords, use secrets management, least-privilege DB roles, and HTTPS for hosted Streamlit.

---

## Troubleshooting

| Issue | What to check |
|--------|----------------|
| `column ... does not exist` (e.g. `Barcode`) | Run `migration_add_barcode_store_settings.sql` or `rebuild_retail_grocery_db.sql`. |
| `SupplierDeliveries` / supplier tabs missing | Run **`migration_supplier_logistics.sql`** (or full `rebuild_retail_grocery_db.sql`). |
| `StreamlitSecretNotFoundError` | Fixed in `database.py` with env fallbacks; or add `.streamlit/secrets.toml`. |
| `psql` not found | Use full path: `C:\Program Files\PostgreSQL\<version>\bin\psql.exe`. |
| Sidebar shows no pages | Ensure `.streamlit/config.toml` exists and Streamlit ≥ 1.33. |
| PDF / `fpdf2` errors | `pip install -r requirements.txt`. |

---

## Optional next steps

- Password hashing (e.g. bcrypt) and migration of stored credentials  
- Persist generated PDFs or object storage for long-term archive (currently on-demand from DB)  
- Deeper analytics (margins, supplier spend, slow movers) and scheduled exports  
- Mobile-friendly layouts for POS on tablets  
- Automated DB backups and monitoring  
- Automated tests and CI  

---

## Feature verification (what this repo implements)

| Area | Status |
|------|--------|
| **Supplier management (manager)** | **Yes** — `pages/Manage_Suppliers.py` + `POSSystem` supplier CRUD and linked products. |
| **Login redirect & resume** | **Yes** — `User.check_login(..., redirect_page=...)` + `intended_page` in `app.py` after successful login. |
| **User management** | **Yes** — create users; **activate/deactivate**; **Password reset** tab (`StaffAdmin.update_user_password`); store cart-removal PIN tab. |
| **Supplier deliveries & AP invoices** | **Yes** — `SupplierDeliveries` / `SupplierDeliveryLines` / `SupplierInvoices`; UI under **Manage Suppliers**; run **`migration_supplier_logistics.sql`** on existing DBs. |
| **Restock email drafts** | **Yes** — templates in **StoreSettings**; `mailto:` + file download from **Manage Suppliers → Restock email**. |
