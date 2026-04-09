-- ========================================================
-- CAVENDISH UNIVERSITY ZAMBIA - PROJECT SCRIPT (POSTGRESQL)
-- Retail Inventory & Sales Management System
-- ========================================================

-- 1. TABLE CREATION (Normalized to 3NF with Role-Based Access)

-- Users table for authentication and role management
CREATE TABLE Users (
    UserID SERIAL PRIMARY KEY,
    Username VARCHAR(50) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL, -- Will store hashed passwords
    FullName VARCHAR(100) NOT NULL,
    Role VARCHAR(20) NOT NULL CHECK (Role IN ('cashier', 'manager')),
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastLogin TIMESTAMP
);

-- Suppliers table
CREATE TABLE Suppliers (
    SupplierID SERIAL PRIMARY KEY,
    SupplierName VARCHAR(100) NOT NULL,
    ContactPerson VARCHAR(100),
    PhoneNumber VARCHAR(15) UNIQUE,
    Email VARCHAR(100),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE Products (
    ProductID SERIAL PRIMARY KEY,
    ProductName VARCHAR(100) NOT NULL,
    Category VARCHAR(50),
    SellingPrice DECIMAL(10,2) NOT NULL,
    SupplierID INT,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastPriceUpdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastPriceUpdatedBy INT,
    FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID) ON DELETE SET NULL,
    FOREIGN KEY (LastPriceUpdatedBy) REFERENCES Users(UserID)
);

-- Stock table
CREATE TABLE Stock (
    StockID SERIAL PRIMARY KEY,
    ProductID INT UNIQUE,
    QuantityAvailable INT DEFAULT 0,
    ReorderLevel INT DEFAULT 10,
    LastRestockDate DATE,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID) ON DELETE CASCADE
);

-- Sales table (removed CustomerID as per requirements)
CREATE TABLE Sales (
    SaleID SERIAL PRIMARY KEY,
    SaleDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    TotalAmount DECIMAL(10,2) NOT NULL,
    ProcessedBy INT,
    PaymentMethod VARCHAR(20) DEFAULT 'cash',
    FOREIGN KEY (ProcessedBy) REFERENCES Users(UserID)
);

-- Sales_Details table
CREATE TABLE Sales_Details (
    SaleDetailID SERIAL PRIMARY KEY,
    SaleID INT,
    ProductID INT,
    QuantitySold INT NOT NULL,
    UnitPrice DECIMAL(10,2) NOT NULL,
    LineTotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (SaleID) REFERENCES Sales(SaleID) ON DELETE CASCADE,
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID) ON DELETE CASCADE
);

-- ========================================================
-- 2. DATA POPULATION
-- ========================================================

-- Default users
INSERT INTO Users (Username, Password, FullName, Role) VALUES
('cashier1', 'cashier123', 'John Cashier', 'cashier'),
('manager1', 'manager123', 'Sarah Manager', 'manager');

-- Sample suppliers
INSERT INTO Suppliers (SupplierName, ContactPerson, PhoneNumber, Email) VALUES
('Trade Kings', 'John Banda', '0977123456', 'sales@tradekings.co.zm'),
('Zambeef Products', 'Mary Phiri', '0966123456', 'orders@zambeef.co.zm'),
('National Milling', 'Peter Zulu', '0955123456', 'info@nationalmilling.co.zm'),
('Unilever Zambia', 'Grace Mwanza', '0978123456', 'procurement@unilever.co.zm');

-- Sample products
INSERT INTO Products (ProductName, Category, SellingPrice, SupplierID) VALUES
('Boom Washing Paste (400g)', 'Cleaning', 25.50, 1),
('Zambeef Mixed Cut (1kg)', 'Meat', 85.00, 2),
('Ndovu Sugar (2kg)', 'Groceries', 65.00, 1),
('Blueband Margarine (500g)', 'Groceries', 35.00, 3),
('Sunlight Soap (200g)', 'Cleaning', 12.50, 4),
('Zambeef Sausage (500g)', 'Meat', 45.00, 2),
('Indomie Noodles (Pack)', 'Groceries', 28.00, 1),
('Close Up Toothpaste (100ml)', 'Personal Care', 18.50, 4),
('Milo Cereal (900g)', 'Groceries', 75.00, 3),
('Surf Washing Powder (1kg)', 'Cleaning', 42.00, 4);

-- Sample stock data
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

-- ========================================================
-- 3. ADVANCED POSTGRESQL FEATURES (Views & Triggers)
-- ========================================================

-- View for Daily Sales Summary
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

-- View for Low Stock Alerts
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
ORDER BY s.QuantityAvailable ASC;

-- View for Product Catalog with Stock
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

-- PostgreSQL Trigger Function for Automated Inventory Updates
CREATE OR REPLACE FUNCTION trg_after_sale_update_stock()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Stock
    SET QuantityAvailable = QuantityAvailable - NEW.QuantitySold
    WHERE ProductID = NEW.ProductID;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach Trigger to Table
CREATE TRIGGER trg_AfterSale_UpdateStock
AFTER INSERT ON Sales_Details
FOR EACH ROW
EXECUTE FUNCTION trg_after_sale_update_stock();

-- Trigger for Price Update Tracking
CREATE OR REPLACE FUNCTION trg_before_product_price_update()
RETURNS TRIGGER AS $$
BEGIN
    -- Only managers can update prices (this will be enforced in application logic)
    NEW.LastPriceUpdate = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_BeforeProductPriceUpdate
BEFORE UPDATE OF SellingPrice ON Products
FOR EACH ROW
EXECUTE FUNCTION trg_before_product_price_update();

-- ========================================================
-- 4. INDEXES FOR PERFORMANCE
-- ========================================================

CREATE INDEX idx_products_category ON Products(Category);
CREATE INDEX idx_products_supplier ON Products(SupplierID);
CREATE INDEX idx_sales_date ON Sales(SaleDate);
CREATE INDEX idx_sales_details_sale ON Sales_Details(SaleID);
CREATE INDEX idx_stock_product ON Stock(ProductID);
CREATE INDEX idx_users_username ON Users(Username);
CREATE INDEX idx_users_role ON Users(Role);

-- ========================================================
-- 5. SAMPLE SALES DATA (For Testing Reports)
-- ========================================================

-- Sample sales for today
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

-- ========================================================
-- END OF SCRIPT
-- ========================================================
