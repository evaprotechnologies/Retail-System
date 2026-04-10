-- Optional sample data: delivery notes (goods-in) + supplier AP invoices.
-- Requires: migration_supplier_logistics.sql (or full rebuild) applied.
-- Safe to run once: skips if reference GRNs GRN-DEMO-001 / GRN-DEMO-002 already exist.

BEGIN;

DO $$
DECLARE
    v_mgr   INT;
    s_trade INT;
    s_zam   INT;
    s_unl   INT;
    p_tk_a  INT;
    p_tk_b  INT;
    p_z_a   INT;
    p_z_b   INT;
    d1      INT;
    d2      INT;
    amt1    NUMERIC(12, 2);
    amt2    NUMERIC(12, 2);
BEGIN
    IF EXISTS (
        SELECT 1 FROM SupplierDeliveries
        WHERE ReferenceCode IN ('GRN-DEMO-001', 'GRN-DEMO-002')
    ) THEN
        RAISE NOTICE 'Sample supplier logistics already present (GRN-DEMO-001/002); skipping.';
        RETURN;
    END IF;

    SELECT UserID INTO v_mgr FROM Users WHERE Role = 'manager' ORDER BY UserID LIMIT 1;
    IF v_mgr IS NULL THEN
        RAISE NOTICE 'No manager user found; skipping sample supplier logistics.';
        RETURN;
    END IF;

    SELECT SupplierID INTO s_trade FROM Suppliers WHERE SupplierName ILIKE '%Trade Kings%' ORDER BY SupplierID LIMIT 1;
    SELECT SupplierID INTO s_zam FROM Suppliers WHERE SupplierName ILIKE '%Zambeef%' ORDER BY SupplierID LIMIT 1;
    SELECT SupplierID INTO s_unl FROM Suppliers WHERE SupplierName ILIKE '%Unilever%' ORDER BY SupplierID LIMIT 1;

    IF s_trade IS NULL OR s_zam IS NULL THEN
        RAISE NOTICE 'Expected suppliers (Trade Kings, Zambeef) not found; skipping.';
        RETURN;
    END IF;

    SELECT ProductID INTO p_tk_a FROM Products WHERE SupplierID = s_trade ORDER BY ProductID LIMIT 1 OFFSET 0;
    SELECT ProductID INTO p_tk_b FROM Products WHERE SupplierID = s_trade ORDER BY ProductID LIMIT 1 OFFSET 1;
    IF p_tk_b IS NULL THEN
        p_tk_b := p_tk_a;
    END IF;

    SELECT ProductID INTO p_z_a FROM Products WHERE SupplierID = s_zam ORDER BY ProductID LIMIT 1 OFFSET 0;
    SELECT ProductID INTO p_z_b FROM Products WHERE SupplierID = s_zam ORDER BY ProductID LIMIT 1 OFFSET 1;
    IF p_z_b IS NULL THEN
        p_z_b := p_z_a;
    END IF;

    INSERT INTO SupplierDeliveries (SupplierID, DeliveryDate, ReferenceCode, Notes, CreatedBy)
    VALUES (s_trade, CURRENT_DATE - 6, 'GRN-DEMO-001', 'Sample goods-in — Trade Kings', v_mgr)
    RETURNING DeliveryID INTO d1;

    INSERT INTO SupplierDeliveries (SupplierID, DeliveryDate, ReferenceCode, Notes, CreatedBy)
    VALUES (s_zam, CURRENT_DATE - 4, 'GRN-DEMO-002', 'Sample goods-in — Zambeef', v_mgr)
    RETURNING DeliveryID INTO d2;

    INSERT INTO SupplierDeliveryLines (DeliveryID, ProductID, QuantityReceived, UnitCost) VALUES
        (d1, p_tk_a, 20, 19.50),
        (d1, p_tk_b, 15, 24.00),
        (d2, p_z_a, 10, 75.00),
        (d2, p_z_b, 8, 82.00);

    UPDATE Stock s SET
        QuantityAvailable = s.QuantityAvailable + agg.added,
        LastRestockDate = GREATEST(COALESCE(s.LastRestockDate, CURRENT_DATE - 6), CURRENT_DATE - 6)
    FROM (
        SELECT pid, SUM(qty)::INT AS added
        FROM (VALUES
            (p_tk_a, 20),
            (p_tk_b, 15),
            (p_z_a, 10),
            (p_z_b, 8)
        ) AS v(pid, qty)
        GROUP BY pid
    ) agg
    WHERE s.ProductID = agg.pid;

    amt1 := 20 * 19.50 + 15 * 24.00;
    amt2 := 10 * 75.00 + 8 * 82.00;

    INSERT INTO SupplierInvoices (SupplierID, InvoiceNumber, InvoiceDate, DueDate, Amount, Status, PaidDate, Notes, DeliveryID)
    VALUES
        (s_trade, 'DEMO-TK-INV-001', CURRENT_DATE - 6, CURRENT_DATE + INTERVAL '30 days', amt1, 'pending', NULL, 'Sample AP — linked to GRN-DEMO-001', d1),
        (s_zam, 'DEMO-ZB-INV-001', CURRENT_DATE - 4, CURRENT_DATE + INTERVAL '30 days', amt2, 'paid', CURRENT_DATE - 1, 'Sample AP — paid', d2);

    IF s_unl IS NOT NULL THEN
        INSERT INTO SupplierInvoices (SupplierID, InvoiceNumber, InvoiceDate, DueDate, Amount, Status, Notes, DeliveryID)
        VALUES (s_unl, 'DEMO-UNL-INV-001', CURRENT_DATE - 10, CURRENT_DATE + INTERVAL '20 days', 2100.00, 'pending', 'Sample standalone AP (no delivery)', NULL);
    END IF;

    RAISE NOTICE 'Inserted sample supplier logistics (GRN-DEMO-001, GRN-DEMO-002).';
END $$;

COMMIT;
