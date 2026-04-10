-- Supplier logistics: delivery notes (goods-in) and accounts-payable style supplier invoices.
-- Run on existing databases after core schema exists.

BEGIN;

CREATE TABLE IF NOT EXISTS SupplierDeliveries (
    DeliveryID SERIAL PRIMARY KEY,
    SupplierID INT NOT NULL REFERENCES Suppliers(SupplierID) ON DELETE RESTRICT,
    DeliveryDate DATE NOT NULL DEFAULT CURRENT_DATE,
    ReferenceCode VARCHAR(80),
    Notes TEXT,
    CreatedBy INT REFERENCES Users(UserID) ON DELETE SET NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS SupplierDeliveryLines (
    LineID SERIAL PRIMARY KEY,
    DeliveryID INT NOT NULL REFERENCES SupplierDeliveries(DeliveryID) ON DELETE CASCADE,
    ProductID INT NOT NULL REFERENCES Products(ProductID) ON DELETE RESTRICT,
    QuantityReceived INT NOT NULL CHECK (QuantityReceived > 0),
    UnitCost DECIMAL(12,2)
);

CREATE TABLE IF NOT EXISTS SupplierInvoices (
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

CREATE INDEX IF NOT EXISTS idx_supplier_deliveries_supplier ON SupplierDeliveries(SupplierID);
CREATE INDEX IF NOT EXISTS idx_supplier_deliveries_date ON SupplierDeliveries(DeliveryDate);
CREATE INDEX IF NOT EXISTS idx_supplier_invoices_supplier ON SupplierInvoices(SupplierID);
CREATE INDEX IF NOT EXISTS idx_supplier_invoices_status ON SupplierInvoices(Status);

INSERT INTO StoreSettings (SettingKey, SettingValue) VALUES
(
    'store_display_name',
    'Retail Supermarket'
),
(
    'restock_email_subject',
    'Restock request — {store_name} (low stock)'
),
(
    'restock_email_body',
    E'Dear {supplier_name},\n\nPlease arrange supply for the following items at or below reorder level at {store_name}:\n\n{items_table}\n\nPlease confirm availability, pricing, and delivery schedule.\n\nKind regards,\nStore Management\n{store_name}'
)
ON CONFLICT (SettingKey) DO NOTHING;

COMMIT;
