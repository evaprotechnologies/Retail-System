# Retail Inventory & Sales Management System

A Streamlit + PostgreSQL retail platform for grocery-style operations, with **role-based access** for **Manager** and **Cashier** users, an **object-oriented** data layer, **barcode-aware POS**, **PDF customer invoices**, and **audit-friendly** reporting.

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
│   ├── store_settings.py           # StoreSettings — cart removal PIN
│   └── navigation.py               # Role-based sidebar (st.page_link)
│
├── pages/
│   ├── Dashboard.py                # Manager — low stock + catalog
│   ├── Manage_Products.py          # Manager — products + barcodes
│   ├── Point_of_Sale.py            # POS — browse / barcode / scanner, cart PIN
│   ├── Sales_Analytics.py          # Manager — daily sales view
│   ├── Manage_Users.py             # Manager — staff, cashier drill-down, PIN tab
│   ├── Cashier_Handover.py         # Cashier — own sales + invoice PDF
│   └── Invoices_Audit.py           # Manager — all sales + invoice PDF / audit
│
└── utils/                          # Legacy (optional); app uses models/ instead
    └── db.py
```

---

## Features (Current)

### Authentication & navigation

- Login via `User.authenticate()`; session stores `current_user` (`Manager` or `Cashier`) plus legacy keys for compatibility.
- **`User.check_login([roles])`** on protected pages.
- **Custom sidebar** (`models/navigation.py`): default Streamlit page list is hidden (`.streamlit/config.toml`). Each role sees only its links + **Logout**.

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
- **Manage Products** — add/update/delete; **unique barcode** per SKU.
- **Sales Analytics** — KPIs from `View_DailySales_Summary`.
- **Manage Users** — create cashiers/managers, activate/deactivate, per-cashier sales + **Sales_Details**; tab to **change store cart-removal PIN**.

### Database (current schema)

| Table / object | Purpose |
|----------------|---------|
| **Users** | Staff accounts, roles `cashier` \| `manager`, `IsActive`, `LastLogin` |
| **StoreSettings** | Key/value (e.g. `cart_removal_pin`) |
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
| `StreamlitSecretNotFoundError` | Fixed in `database.py` with env fallbacks; or add `.streamlit/secrets.toml`. |
| `psql` not found | Use full path: `C:\Program Files\PostgreSQL\<version>\bin\psql.exe`. |
| Sidebar shows no pages | Ensure `.streamlit/config.toml` exists and Streamlit ≥ 1.33. |
| PDF / `fpdf2` errors | `pip install -r requirements.txt`. |

---

## Optional next steps

- Password hashing (e.g. bcrypt) and migration of stored credentials  
- Persist generated PDFs or object storage for long-term archive (currently on-demand from DB)  
- Automated tests and CI  
