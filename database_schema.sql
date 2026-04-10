-- ========================================================
-- CAVENDISH UNIVERSITY ZAMBIA - PROJECT SCRIPT (POSTGRESQL)
-- Retail Inventory & Sales Management System
-- ========================================================
-- This file defines the CURRENT application database schema
-- (aligned with rebuild_retail_grocery_db.sql and the Streamlit app).
--
-- Choose one:
--   • Fresh install / teaching demo: run this script on an empty database.
--   • Full supermarket seed (32+ products): use rebuild_retail_grocery_db.sql
--   • Existing DB missing barcode / StoreSettings: migration_add_barcode_store_settings.sql
-- ========================================================

-- ========================================================
-- 1. TABLE CREATION
-- ========================================================

CREATE TABLE Users (
    UserID SERIAL PRIMARY KEY,
    Username VARCHAR(50) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL,
    FullName VARCHAR(100) NOT NULL,
    Role VARCHAR(20) NOT NULL CHECK (Role IN ('cashier', 'manager')),
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastLogin TIMESTAMP
);

-- Store-wide settings (e.g. cart removal PIN — not user login passwords)
CREATE TABLE StoreSettings (
    SettingKey VARCHAR(50) PRIMARY KEY,
    SettingValue TEXT NOT NULL
);

CREATE TABLE Suppliers (
    SupplierID SERIAL PRIMARY KEY,
    SupplierName VARCHAR(100) NOT NULL,
    ContactPerson VARCHAR(100),
    PhoneNumber VARCHAR(20) UNIQUE,
    Email VARCHAR(100),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Products (
    ProductID SERIAL PRIMARY KEY,
    ProductName VARCHAR(120) NOT NULL,
    Barcode VARCHAR(32) UNIQUE NOT NULL,
    Category VARCHAR(50) NOT NULL,
    SellingPrice DECIMAL(10,2) NOT NULL CHECK (SellingPrice > 0),
    SupplierID INT,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastPriceUpdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastPriceUpdatedBy INT,
    FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID) ON DELETE SET NULL,
    FOREIGN KEY (LastPriceUpdatedBy) REFERENCES Users(UserID) ON DELETE SET NULL
);

CREATE TABLE Stock (
    StockID SERIAL PRIMARY KEY,
    ProductID INT UNIQUE NOT NULL,
    QuantityAvailable INT NOT NULL DEFAULT 0 CHECK (QuantityAvailable >= 0),
    ReorderLevel INT NOT NULL DEFAULT 10 CHECK (ReorderLevel >= 0),
    LastRestockDate DATE,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID) ON DELETE CASCADE
);

CREATE TABLE Sales (
    SaleID SERIAL PRIMARY KEY,
    SaleDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    TotalAmount DECIMAL(10,2) NOT NULL CHECK (TotalAmount >= 0),
    ProcessedBy INT,
    PaymentMethod VARCHAR(20) DEFAULT 'cash' CHECK (PaymentMethod IN ('cash', 'card', 'mobile_money')),
    FOREIGN KEY (ProcessedBy) REFERENCES Users(UserID) ON DELETE SET NULL
);

CREATE TABLE Sales_Details (
    SaleDetailID SERIAL PRIMARY KEY,
    SaleID INT NOT NULL,
    ProductID INT NOT NULL,
    QuantitySold INT NOT NULL CHECK (QuantitySold > 0),
    UnitPrice DECIMAL(10,2) NOT NULL CHECK (UnitPrice >= 0),
    LineTotal DECIMAL(10,2) NOT NULL CHECK (LineTotal >= 0),
    FOREIGN KEY (SaleID) REFERENCES Sales(SaleID) ON DELETE CASCADE,
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID) ON DELETE RESTRICT
);

CREATE TABLE SupplierDeliveries (
    DeliveryID SERIAL PRIMARY KEY,
    SupplierID INT NOT NULL REFERENCES Suppliers(SupplierID) ON DELETE RESTRICT,
    DeliveryDate DATE NOT NULL DEFAULT CURRENT_DATE,
    ReferenceCode VARCHAR(80),
    Notes TEXT,
    CreatedBy INT REFERENCES Users(UserID) ON DELETE SET NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE SupplierDeliveryLines (
    LineID SERIAL PRIMARY KEY,
    DeliveryID INT NOT NULL REFERENCES SupplierDeliveries(DeliveryID) ON DELETE CASCADE,
    ProductID INT NOT NULL REFERENCES Products(ProductID) ON DELETE RESTRICT,
    QuantityReceived INT NOT NULL CHECK (QuantityReceived > 0),
    UnitCost DECIMAL(12,2)
);

CREATE TABLE SupplierInvoices (
    InvoiceID SERIAL PRIMARY KEY,
    SupplierID INT NOT NULL REFERENCES Suppliers(SupplierID) ON DELETE RESTRICT,
    InvoiceNumber VARCHAR(80) NOT NULL,
    InvoiceDate DATE NOT NULL DEFAULT CURRENT_DATE,
    DueDate DATE,
    Amount DECIMAL(12,2) NOT NULL CHECK (Amount >= 0),
    Status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (Status IN ('pending', 'paid', 'cancelled')),
    PaidDate DATE,
    Notes TEXT,
    DeliveryID INT REFERENCES SupplierDeliveries(DeliveryID) ON DELETE SET NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (SupplierID, InvoiceNumber)
);

-- ========================================================
-- 2. INDEXES
-- ========================================================

CREATE INDEX idx_users_username ON Users(Username);
CREATE INDEX idx_users_role ON Users(Role);
CREATE INDEX idx_products_category ON Products(Category);
CREATE INDEX idx_products_supplier ON Products(SupplierID);
CREATE INDEX idx_products_barcode ON Products(Barcode);
CREATE INDEX idx_stock_product ON Stock(ProductID);
CREATE INDEX idx_sales_date ON Sales(SaleDate);
CREATE INDEX idx_sales_details_sale ON Sales_Details(SaleID);
CREATE INDEX idx_supplier_deliveries_supplier ON SupplierDeliveries(SupplierID);
CREATE INDEX idx_supplier_deliveries_date ON SupplierDeliveries(DeliveryDate);
CREATE INDEX idx_supplier_invoices_supplier ON SupplierInvoices(SupplierID);
CREATE INDEX idx_supplier_invoices_status ON SupplierInvoices(Status);

-- ========================================================
-- 3. TRIGGER FUNCTIONS & TRIGGERS
-- ========================================================

CREATE OR REPLACE FUNCTION trg_after_sale_update_stock()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Stock
    SET QuantityAvailable = GREATEST(QuantityAvailable - NEW.QuantitySold, 0)
    WHERE ProductID = NEW.ProductID;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_AfterSale_UpdateStock
AFTER INSERT ON Sales_Details
FOR EACH ROW
EXECUTE FUNCTION trg_after_sale_update_stock();

CREATE OR REPLACE FUNCTION trg_before_product_price_update()
RETURNS TRIGGER AS $$
BEGIN
    NEW.LastPriceUpdate = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_BeforeProductPriceUpdate
BEFORE UPDATE OF SellingPrice ON Products
FOR EACH ROW
EXECUTE FUNCTION trg_before_product_price_update();

-- ========================================================
-- 4. VIEWS
-- ========================================================

CREATE OR REPLACE VIEW View_DailySales_Summary AS
SELECT
    DATE(s.SaleDate) AS TransactionDate,
    COUNT(DISTINCT s.SaleID) AS TotalInvoices,
    SUM(sd.QuantitySold) AS TotalItemsSold,
    SUM(sd.LineTotal) AS DailyRevenue,
    COUNT(DISTINCT s.ProcessedBy) AS StaffInvolved
FROM Sales s
JOIN Sales_Details sd ON s.SaleID = sd.SaleID
GROUP BY DATE(s.SaleDate);

CREATE OR REPLACE VIEW View_LowStock_Alerts AS
SELECT
    p.ProductID,
    p.ProductName,
    p.Category,
    s.QuantityAvailable,
    s.ReorderLevel,
    sup.SupplierName,
    sup.PhoneNumber
FROM Products p
JOIN Stock s ON p.ProductID = s.ProductID
LEFT JOIN Suppliers sup ON p.SupplierID = sup.SupplierID
WHERE s.QuantityAvailable <= s.ReorderLevel
ORDER BY s.QuantityAvailable ASC, p.ProductName ASC;

CREATE OR REPLACE VIEW View_Product_Catalog AS
SELECT
    p.ProductID,
    p.ProductName,
    p.Barcode,
    p.Category,
    p.SellingPrice,
    COALESCE(s.QuantityAvailable, 0) AS StockLevel,
    s.ReorderLevel,
    sup.SupplierName,
    p.LastPriceUpdate,
    u.FullName AS LastUpdatedBy
FROM Products p
LEFT JOIN Stock s ON p.ProductID = s.ProductID
LEFT JOIN Suppliers sup ON p.SupplierID = sup.SupplierID
LEFT JOIN Users u ON p.LastPriceUpdatedBy = u.UserID
ORDER BY p.ProductName;

-- ========================================================
-- 5. SAMPLE DATA (compact demo set)
-- ========================================================

INSERT INTO Users (Username, Password, FullName, Role) VALUES
('cashier1', 'cashier123', 'John Cashier', 'cashier'),
('manager1', 'manager123', 'Sarah Manager', 'manager');

INSERT INTO StoreSettings (SettingKey, SettingValue) VALUES
('cart_removal_pin', '882244'),
('store_display_name', 'Retail Supermarket'),
('restock_email_subject', 'Restock request — {store_name} (low stock)'),
(
    'restock_email_body',
    E'Dear {supplier_name},\n\nPlease arrange supply for the following items at or below reorder level at {store_name}:\n\n{items_table}\n\nPlease confirm availability, pricing, and delivery schedule.\n\nKind regards,\nStore Management\n{store_name}'
);

INSERT INTO Suppliers (SupplierName, ContactPerson, PhoneNumber, Email) VALUES
('Trade Kings', 'John Banda', '0977123456', 'sales@tradekings.co.zm'),
('Zambeef Products', 'Mary Phiri', '0966123456', 'orders@zambeef.co.zm'),
('National Milling', 'Peter Zulu', '0955123456', 'info@nationalmilling.co.zm'),
('Unilever Zambia', 'Grace Mwanza', '0978123456', 'procurement@unilever.co.zm');

INSERT INTO Products (ProductName, Barcode, Category, SellingPrice, SupplierID, LastPriceUpdatedBy) VALUES
('Boom Washing Paste (400g)', '6001000000001', 'Cleaning', 25.50, 1, 2),
('Zambeef Mixed Cut (1kg)', '6001000000002', 'Meat', 85.00, 2, 2),
('Ndovu Sugar (2kg)', '6001000000003', 'Groceries', 65.00, 1, 2),
('Blueband Margarine (500g)', '6001000000004', 'Groceries', 35.00, 3, 2),
('Sunlight Soap (200g)', '6001000000005', 'Cleaning', 12.50, 4, 2),
('Zambeef Sausage (500g)', '6001000000006', 'Meat', 45.00, 2, 2),
('Indomie Noodles (Pack)', '6001000000007', 'Groceries', 28.00, 1, 2),
('Close Up Toothpaste (100ml)', '6001000000008', 'Personal Care', 18.50, 4, 2),
('Milo Cereal (900g)', '6001000000009', 'Groceries', 75.00, 3, 2),
('Surf Washing Powder (1kg)', '6001000000010', 'Cleaning', 42.00, 4, 2);

INSERT INTO Stock (ProductID, QuantityAvailable, ReorderLevel, LastRestockDate) VALUES
(1, 150, 20, '2026-04-01'),
(2, 45, 15, '2026-04-02'),
(3, 15, 30, '2026-04-03'),
(4, 80, 25, '2026-04-01'),
(5, 200, 30, '2026-04-02'),
(6, 60, 20, '2026-04-03'),
(7, 120, 40, '2026-04-01'),
(8, 90, 15, '2026-04-02'),
(9, 35, 10, '2026-04-03'),
(10, 75, 20, '2026-04-01');

INSERT INTO Sales (TotalAmount, ProcessedBy, PaymentMethod) VALUES
(110.50, 1, 'cash'),
(45.00, 1, 'mobile_money'),
(156.50, 1, 'cash');

INSERT INTO Sales_Details (SaleID, ProductID, QuantitySold, UnitPrice, LineTotal) VALUES
(1, 1, 2, 25.50, 51.00),
(1, 4, 1, 35.00, 35.00),
(1, 5, 2, 12.50, 25.00),
(2, 6, 1, 45.00, 45.00),
(3, 2, 1, 85.00, 85.00),
(3, 8, 1, 18.50, 18.50),
(3, 5, 4, 12.50, 50.00);

-- Sample goods-in (delivery notes) + supplier AP invoices (matches app behaviour: stock increases)
INSERT INTO SupplierDeliveries (SupplierID, DeliveryDate, ReferenceCode, Notes, CreatedBy) VALUES
(1, '2026-04-08', 'GRN-2026-0410', 'Cleaning & groceries restock — Trade Kings', 2),
(2, '2026-04-09', 'GRN-2026-0411', 'Meat delivery — Zambeef', 2);

INSERT INTO SupplierDeliveryLines (DeliveryID, ProductID, QuantityReceived, UnitCost) VALUES
(1, 1, 50, 18.00),
(1, 3, 40, 48.00),
(2, 2, 25, 72.00),
(2, 6, 30, 38.00);

UPDATE Stock SET QuantityAvailable = QuantityAvailable + 50, LastRestockDate = '2026-04-08' WHERE ProductID = 1;
UPDATE Stock SET QuantityAvailable = QuantityAvailable + 40, LastRestockDate = '2026-04-08' WHERE ProductID = 3;
UPDATE Stock SET QuantityAvailable = QuantityAvailable + 25, LastRestockDate = '2026-04-09' WHERE ProductID = 2;
UPDATE Stock SET QuantityAvailable = QuantityAvailable + 30, LastRestockDate = '2026-04-09' WHERE ProductID = 6;

INSERT INTO SupplierInvoices (SupplierID, InvoiceNumber, InvoiceDate, DueDate, Amount, Status, PaidDate, Notes, DeliveryID) VALUES
(1, 'TK-INV-2026-0410', '2026-04-08', '2026-05-08', 2820.00, 'pending', NULL, 'Linked to GRN-2026-0410', 1),
(2, 'ZB-INV-2026-0409', '2026-04-09', '2026-05-09', 2940.00, 'paid', '2026-04-10', 'Settled — mobile transfer', 2),
(4, 'UNL-INV-2026-0395', '2026-04-01', '2026-05-01', 1850.50, 'pending', NULL, 'Standalone AP — not tied to a recorded delivery', NULL);

-- ========================================================
-- END OF SCRIPT
-- ========================================================
