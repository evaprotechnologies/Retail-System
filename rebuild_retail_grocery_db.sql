-- ============================================================
-- Retail Grocery DB Rebuild Script (PostgreSQL)
-- Purpose:
--   1) Remove old schema/data
--   2) Recreate schema for updated OOP retail setup
--   3) Seed fresh supermarket-style data
-- ============================================================

BEGIN;

-- ============================================================
-- 0) CLEAN REBUILD: drop old objects
-- ============================================================

DROP TRIGGER IF EXISTS trg_AfterSale_UpdateStock ON Sales_Details;
DROP TRIGGER IF EXISTS trg_BeforeProductPriceUpdate ON Products;

DROP FUNCTION IF EXISTS trg_after_sale_update_stock();
DROP FUNCTION IF EXISTS trg_before_product_price_update();

DROP VIEW IF EXISTS View_DailySales_Summary;
DROP VIEW IF EXISTS View_LowStock_Alerts;
DROP VIEW IF EXISTS View_Product_Catalog;

DROP TABLE IF EXISTS SupplierDeliveryLines CASCADE;
DROP TABLE IF EXISTS SupplierInvoices CASCADE;
DROP TABLE IF EXISTS SupplierDeliveries CASCADE;
DROP TABLE IF EXISTS Sales_Details CASCADE;
DROP TABLE IF EXISTS Sales CASCADE;
DROP TABLE IF EXISTS Stock CASCADE;
DROP TABLE IF EXISTS Products CASCADE;
DROP TABLE IF EXISTS Suppliers CASCADE;
DROP TABLE IF EXISTS Users CASCADE;
DROP TABLE IF EXISTS StoreSettings CASCADE;

-- ============================================================
-- 1) CORE TABLES
-- ============================================================

CREATE TABLE StoreSettings (
    SettingKey VARCHAR(50) PRIMARY KEY,
    SettingValue TEXT NOT NULL
);

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

-- ============================================================
-- 2) PERFORMANCE INDEXES
-- ============================================================

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

-- ============================================================
-- 3) TRIGGERS / FUNCTIONS
-- ============================================================

-- Deduct stock whenever a sale line item is inserted
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

-- Maintain LastPriceUpdate automatically
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

-- ============================================================
-- 4) REPORTING VIEWS
-- ============================================================

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

-- ============================================================
-- 5) SEED DATA (SUPERMARKET / GROCERY)
-- ============================================================

-- Store-level security (cart line removal / clear cart — not login passwords)
INSERT INTO StoreSettings (SettingKey, SettingValue) VALUES
('cart_removal_pin', '882244'),
('store_display_name', 'Retail Supermarket'),
('restock_email_subject', 'Restock request — {store_name} (low stock)'),
(
    'restock_email_body',
    E'Dear {supplier_name},\n\nPlease arrange supply for the following items at or below reorder level at {store_name}:\n\n{items_table}\n\nPlease confirm availability, pricing, and delivery schedule.\n\nKind regards,\nStore Management\n{store_name}'
);

-- Users
INSERT INTO Users (Username, Password, FullName, Role) VALUES
('manager1', 'manager123', 'Sarah Manager', 'manager'),
('manager2', 'manager456', 'Peter Supervisor', 'manager'),
('cashier1', 'cashier123', 'John Cashier', 'cashier'),
('cashier2', 'cashier456', 'Loveness Tembo', 'cashier'),
('cashier3', 'cashier789', 'Kelvin Banda', 'cashier');

-- Suppliers
INSERT INTO Suppliers (SupplierName, ContactPerson, PhoneNumber, Email) VALUES
('FreshFarm Produce Zambia', 'Martha Mwansa', '0977000001', 'orders@freshfarm.co.zm'),
('Trade Kings Distribution', 'John Chola', '0977000002', 'sales@tradekings.co.zm'),
('Zambeef Wholesale', 'Mary Phiri', '0977000003', 'bulk@zambeef.co.zm'),
('National Milling Group', 'Peter Zulu', '0977000004', 'supply@nationalmilling.co.zm'),
('Unilever Consumer Goods', 'Grace Mwanza', '0977000005', 'trade@unilever.co.zm'),
('Dairy Gold Suppliers', 'Brian Nkonde', '0977000006', 'dispatch@dairygold.co.zm');

-- Products (Barcodes: 6001000000001 … unique per SKU)
INSERT INTO Products (ProductName, Barcode, Category, SellingPrice, SupplierID, LastPriceUpdatedBy) VALUES
('White Bread 700g', '6001000000001', 'Bakery', 18.50, 4, 1),
('Brown Bread 700g', '6001000000002', 'Bakery', 20.00, 4, 1),
('Long Grain Rice 2kg', '6001000000003', 'Groceries', 68.00, 4, 1),
('Mealie Meal Breakfast 10kg', '6001000000004', 'Groceries', 180.00, 4, 1),
('Sugar White 2kg', '6001000000005', 'Groceries', 62.00, 4, 1),
('Cooking Oil 2L', '6001000000006', 'Groceries', 95.00, 2, 1),
('Table Salt 1kg', '6001000000007', 'Groceries', 14.00, 2, 1),
('Spaghetti 500g', '6001000000008', 'Groceries', 24.00, 2, 1),
('Canned Baked Beans 420g', '6001000000009', 'Groceries', 19.00, 2, 1),
('Corn Flakes 750g', '6001000000010', 'Groceries', 58.00, 5, 1),
('Fresh Milk 1L', '6001000000011', 'Dairy', 24.50, 6, 1),
('Yoghurt Strawberry 500ml', '6001000000012', 'Dairy', 29.00, 6, 1),
('Cheddar Cheese 250g', '6001000000013', 'Dairy', 55.00, 6, 1),
('Butter 500g', '6001000000014', 'Dairy', 48.00, 6, 1),
('Eggs Tray (30)', '6001000000015', 'Dairy', 85.00, 1, 1),
('Chicken Whole 1.2kg avg', '6001000000016', 'Meat', 92.00, 3, 1),
('Beef Mince 1kg', '6001000000017', 'Meat', 98.00, 3, 1),
('Pork Chops 1kg', '6001000000018', 'Meat', 105.00, 3, 1),
('Apples 1kg', '6001000000019', 'Fresh Produce', 39.00, 1, 1),
('Bananas 1kg', '6001000000020', 'Fresh Produce', 28.00, 1, 1),
('Tomatoes 1kg', '6001000000021', 'Fresh Produce', 26.00, 1, 1),
('Onions 1kg', '6001000000022', 'Fresh Produce', 22.00, 1, 1),
('Potatoes 2kg', '6001000000023', 'Fresh Produce', 36.00, 1, 1),
('Cabbage Each', '6001000000024', 'Fresh Produce', 18.00, 1, 1),
('Laundry Detergent 1kg', '6001000000025', 'Cleaning', 45.00, 2, 1),
('Dishwashing Liquid 750ml', '6001000000026', 'Cleaning', 28.00, 2, 1),
('Bath Soap 175g', '6001000000027', 'Personal Care', 13.50, 5, 1),
('Toothpaste 100ml', '6001000000028', 'Personal Care', 21.00, 5, 1),
('Toilet Paper 10 Pack', '6001000000029', 'Household', 65.00, 5, 1),
('Bottled Water 1.5L', '6001000000030', 'Beverages', 9.00, 2, 1),
('Orange Juice 1L', '6001000000031', 'Beverages', 27.00, 5, 1),
('Soft Drink 2L', '6001000000032', 'Beverages', 19.50, 2, 1);

-- Stock (aligned with ProductID insertion order above)
INSERT INTO Stock (ProductID, QuantityAvailable, ReorderLevel, LastRestockDate) VALUES
(1, 120, 25, CURRENT_DATE - INTERVAL '2 days'),
(2, 95, 20, CURRENT_DATE - INTERVAL '2 days'),
(3, 60, 15, CURRENT_DATE - INTERVAL '3 days'),
(4, 40, 10, CURRENT_DATE - INTERVAL '4 days'),
(5, 55, 15, CURRENT_DATE - INTERVAL '3 days'),
(6, 70, 20, CURRENT_DATE - INTERVAL '1 day'),
(7, 80, 20, CURRENT_DATE - INTERVAL '5 days'),
(8, 50, 15, CURRENT_DATE - INTERVAL '6 days'),
(9, 45, 10, CURRENT_DATE - INTERVAL '4 days'),
(10, 38, 12, CURRENT_DATE - INTERVAL '7 days'),
(11, 48, 12, CURRENT_DATE - INTERVAL '1 day'),
(12, 30, 10, CURRENT_DATE - INTERVAL '2 days'),
(13, 24, 8, CURRENT_DATE - INTERVAL '3 days'),
(14, 28, 8, CURRENT_DATE - INTERVAL '2 days'),
(15, 36, 10, CURRENT_DATE - INTERVAL '1 day'),
(16, 26, 8, CURRENT_DATE - INTERVAL '1 day'),
(17, 18, 8, CURRENT_DATE - INTERVAL '2 days'),
(18, 16, 6, CURRENT_DATE - INTERVAL '2 days'),
(19, 52, 12, CURRENT_DATE - INTERVAL '1 day'),
(20, 64, 20, CURRENT_DATE - INTERVAL '1 day'),
(21, 33, 10, CURRENT_DATE - INTERVAL '1 day'),
(22, 29, 10, CURRENT_DATE - INTERVAL '2 days'),
(23, 22, 8, CURRENT_DATE - INTERVAL '2 days'),
(24, 14, 8, CURRENT_DATE - INTERVAL '1 day'),
(25, 46, 12, CURRENT_DATE - INTERVAL '5 days'),
(26, 34, 10, CURRENT_DATE - INTERVAL '3 days'),
(27, 90, 25, CURRENT_DATE - INTERVAL '5 days'),
(28, 65, 20, CURRENT_DATE - INTERVAL '4 days'),
(29, 40, 10, CURRENT_DATE - INTERVAL '4 days'),
(30, 110, 30, CURRENT_DATE - INTERVAL '2 days'),
(31, 58, 15, CURRENT_DATE - INTERVAL '2 days'),
(32, 76, 20, CURRENT_DATE - INTERVAL '2 days');

-- Starter sales (for analytics/dashboard demos)
INSERT INTO Sales (TotalAmount, ProcessedBy, PaymentMethod, SaleDate) VALUES
(152.00, 3, 'cash', CURRENT_TIMESTAMP - INTERVAL '2 days'),
(89.50, 4, 'mobile_money', CURRENT_TIMESTAMP - INTERVAL '1 day'),
(245.00, 5, 'card', CURRENT_TIMESTAMP - INTERVAL '1 day'),
(128.00, 3, 'cash', CURRENT_TIMESTAMP);

INSERT INTO Sales_Details (SaleID, ProductID, QuantitySold, UnitPrice, LineTotal) VALUES
(1, 1, 2, 18.50, 37.00),
(1, 11, 1, 24.50, 24.50),
(1, 30, 5, 9.00, 45.00),
(1, 27, 2, 13.50, 27.00),

(2, 20, 1, 28.00, 28.00),
(2, 21, 1, 26.00, 26.00),
(2, 22, 1, 22.00, 22.00),
(2, 31, 1, 27.00, 27.00),

(3, 4, 1, 180.00, 180.00),
(3, 6, 1, 95.00, 95.00),

(4, 2, 1, 20.00, 20.00),
(4, 3, 1, 68.00, 68.00),
(4, 8, 1, 24.00, 24.00),
(4, 30, 2, 9.00, 18.00);

-- Sample goods-in (delivery notes) + supplier AP invoices
INSERT INTO SupplierDeliveries (SupplierID, DeliveryDate, ReferenceCode, Notes, CreatedBy) VALUES
(2, CURRENT_DATE - INTERVAL '5 days', 'GRN-2026-0403', 'Groceries & cleaning — Trade Kings', 1),
(3, CURRENT_DATE - INTERVAL '3 days', 'GRN-2026-0405', 'Meat wholesale — Zambeef', 1);

INSERT INTO SupplierDeliveryLines (DeliveryID, ProductID, QuantityReceived, UnitCost) VALUES
(1, 6, 24, 88.00),
(1, 7, 36, 11.50),
(1, 25, 20, 38.00),
(2, 16, 18, 84.00),
(2, 17, 12, 92.00);

UPDATE Stock SET QuantityAvailable = QuantityAvailable + 24, LastRestockDate = CURRENT_DATE - INTERVAL '5 days' WHERE ProductID = 6;
UPDATE Stock SET QuantityAvailable = QuantityAvailable + 36, LastRestockDate = CURRENT_DATE - INTERVAL '5 days' WHERE ProductID = 7;
UPDATE Stock SET QuantityAvailable = QuantityAvailable + 20, LastRestockDate = CURRENT_DATE - INTERVAL '5 days' WHERE ProductID = 25;
UPDATE Stock SET QuantityAvailable = QuantityAvailable + 18, LastRestockDate = CURRENT_DATE - INTERVAL '3 days' WHERE ProductID = 16;
UPDATE Stock SET QuantityAvailable = QuantityAvailable + 12, LastRestockDate = CURRENT_DATE - INTERVAL '3 days' WHERE ProductID = 17;

INSERT INTO SupplierInvoices (SupplierID, InvoiceNumber, InvoiceDate, DueDate, Amount, Status, PaidDate, Notes, DeliveryID) VALUES
(2, 'TK-DIST-INV-240403', CURRENT_DATE - INTERVAL '5 days', CURRENT_DATE + INTERVAL '25 days', 3286.00, 'pending', NULL, 'Matches GRN-2026-0403', 1),
(3, 'ZB-WH-INV-240405', CURRENT_DATE - INTERVAL '3 days', CURRENT_DATE + INTERVAL '30 days', 2616.00, 'paid', CURRENT_DATE - INTERVAL '1 day', 'Paid — bank', 2),
(5, 'UNL-ZM-INV-240390', CURRENT_DATE - INTERVAL '12 days', CURRENT_DATE + INTERVAL '18 days', 12450.75, 'pending', NULL, 'Monthly sundries — no GRN on file', NULL),
(3, 'ZB-WH-INV-240388', CURRENT_DATE - INTERVAL '20 days', CURRENT_DATE - INTERVAL '5 days', 980.00, 'cancelled', NULL, 'Cancelled — duplicate entry', NULL);

COMMIT;

-- ============================================================
-- END
-- ============================================================

