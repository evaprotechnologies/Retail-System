# Retail Inventory & Sales Management System

A Streamlit + PostgreSQL retail platform for store operations, with role-based access for **Manager** and **Cashier** users.

This project includes:
- secure login and role-based page protection
- point-of-sale transaction processing
- inventory and low-stock monitoring
- product CRUD management
- sales analytics reporting
- ongoing migration to an object-oriented architecture (`models/` layer)

---

## Tech Stack

- Python 3.10+
- Streamlit
- PostgreSQL
- `psycopg2-binary`
- Pandas

---

## Project Structure

```text
Retail_System_Project/
├── app.py                    # Login gateway + role-aware landing page
├── database_schema.sql       # Full PostgreSQL schema, views, triggers, sample data
├── requirements.txt          # Python dependencies
│
├── models/                   # OOP business/data access layer (new architecture)
│   ├── __init__.py
│   ├── database.py           # DatabaseConnection class
│   ├── users.py              # User, Manager, Cashier classes
│   └── inventory.py          # POSSystem class for inventory and sales
│
├── pages/                    # Streamlit UI pages
│   ├── Dashboard.py          # Manager-only inventory dashboard
│   ├── Manage_Products.py    # Manager-only product CRUD
│   ├── Point_of_Sale.py      # POS terminal (cashier/manager)
│   └── Sales_Analytics.py    # Manager-only sales reports
│
└── utils/                    # Legacy functional helpers (being migrated to models/)
    └── db.py
```

---

## Architecture Overview

The codebase is transitioning from a functional style to a cleaner OOP structure:

- **UI Layer (`app.py`, `pages/`)**
  - Handles rendering, forms, user interactions, and Streamlit session state.
- **Business/Data Access Layer (`models/`)**
  - Encapsulates SQL and database transactions in classes.
  - Exposes high-level methods like `User.authenticate()` and `POSSystem.process_transaction()`.
- **Database Layer (PostgreSQL)**
  - Stores users, products, stock, and sales.
  - Includes SQL views and triggers for analytics and stock updates.

### Why this structure matters

- Better separation of concerns
- Easier testing and maintenance
- Reusable business logic across pages
- Cleaner role boundaries with class-based behaviors

---

## Core OOP Classes

### `models/database.py`
- `DatabaseConnection`
  - centralizes DB credentials
  - provides helper methods:
    - `fetch_one(...)`
    - `fetch_all(...)`
    - `execute_query(...)`

### `models/users.py`
- `User`
  - base class with common user properties
  - static `authenticate(username, password)`
- `Manager(User)`
  - privileged actions (for example manager override checks)
- `Cashier(User)`
  - standard POS operations

### `models/inventory.py`
- `POSSystem`
  - product retrieval methods
  - sale processing transaction methods

---

## Features by Role

### Cashier
- Login to employee portal
- Access Point of Sale
- Search/select products
- Manage cart and complete sales

### Manager
- All cashier capabilities
- View inventory dashboard
- Manage products (add/update/delete)
- View analytics and KPI reports
- Perform manager override checks where required

---

## Database Design Highlights

Defined in `database_schema.sql`:

- **Tables:** `Users`, `Suppliers`, `Products`, `Stock`, `Sales`, `Sales_Details`
- **Views:**
  - `View_DailySales_Summary`
  - `View_LowStock_Alerts`
  - `View_Product_Catalog`
- **Triggers:**
  - automatic stock deduction after each sale detail insert
  - product price update timestamp tracking
- **Indexes:** performance-focused indexes on frequently queried fields

---

## Setup Instructions (Windows / PowerShell)

## 1) Clone or open the project

```powershell
cd "c:\Users\Apollo IT\Documents\DevHub\Retail_System_Project"
```

## 2) Create and activate virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3) Install dependencies

```powershell
pip install -r requirements.txt
```

## 4) Prepare PostgreSQL database

Create the database (if not already created):

```sql
CREATE DATABASE retailsystemdb;
```

Run the schema script:

```powershell
psql -U postgres -d retailsystemdb -f database_schema.sql
```

## 5) Configure database credentials

Current defaults are loaded from:
- Streamlit secrets (preferred), or
- environment variables, or
- fallback defaults in `models/database.py`

Recommended environment variables:

```powershell
$env:DB_HOST="localhost"
$env:DB_NAME="retailsystemdb"
$env:DB_USER="postgres"
$env:DB_PASSWORD="your_password"
$env:DB_PORT="5432"
```

## 6) Run the app

```powershell
streamlit run app.py
```

---

## Default Test Accounts

Loaded by `database_schema.sql`:

- Cashier: `cashier1` / `cashier123`
- Manager: `manager1` / `manager123`

---

## Current Migration Status

- `app.py` and `pages/Point_of_Sale.py` now use the OOP `models/` layer.
- Other manager pages still use legacy helpers from `utils/db.py`.
- Next recommended step: migrate `Dashboard.py`, `Manage_Products.py`, and `Sales_Analytics.py` into class-based services under `models/`, then retire `utils/`.

---

## Security Notes

- Current sample data uses plain-text passwords for development convenience.
- For production, implement strong password hashing and salted verification (for example `bcrypt`).
- Restrict DB credentials using Streamlit secrets or secure environment management.
- Apply least-privilege DB user permissions.

---

## Troubleshooting

- **Cannot connect to DB**
  - Confirm PostgreSQL service is running.
  - Check DB host, port, username, password, and database name.
- **Login fails for test users**
  - Re-run `database_schema.sql` in the correct database.
- **Module import errors**
  - Ensure virtual environment is activated and dependencies installed.

---

## Future Improvements

- Complete OOP migration for all pages
- Add password hashing/auth hardening
- Add unit tests and integration tests
- Introduce audit logging for privileged actions
- Add CI pipeline and code quality checks

