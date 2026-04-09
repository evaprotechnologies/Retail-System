-- Run once on an existing database that predates Barcode + StoreSettings.
-- Safe to re-run only if you adjust conditions; for production use a proper migration tool.

BEGIN;

CREATE TABLE IF NOT EXISTS StoreSettings (
    SettingKey VARCHAR(50) PRIMARY KEY,
    SettingValue TEXT NOT NULL
);

INSERT INTO StoreSettings (SettingKey, SettingValue)
VALUES ('cart_removal_pin', '882244')
ON CONFLICT (SettingKey) DO NOTHING;

ALTER TABLE Products ADD COLUMN IF NOT EXISTS Barcode VARCHAR(32);

UPDATE Products SET Barcode = '60010000' || LPAD(ProductID::TEXT, 6, '0')
WHERE Barcode IS NULL OR TRIM(Barcode) = '';

ALTER TABLE Products ALTER COLUMN Barcode SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_products_barcode ON Products(Barcode);

COMMIT;
