"""Supplier delivery notes (goods-in) and supplier invoices (AP tracking)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from models.database import DatabaseConnection
from models.store_settings import StoreSettings

db = DatabaseConnection()

STORE_DISPLAY_KEY = "store_display_name"
RESTOCK_SUBJECT_KEY = "restock_email_subject"
RESTOCK_BODY_KEY = "restock_email_body"


class SupplierLogistics:
    @staticmethod
    def list_deliveries(limit: int = 200):
        return db.fetch_all(
            """
            SELECT d.DeliveryID, d.SupplierID, s.SupplierName, d.DeliveryDate, d.ReferenceCode,
                   d.Notes, d.CreatedAt, u.FullName AS CreatedByName
            FROM SupplierDeliveries d
            JOIN Suppliers s ON s.SupplierID = d.SupplierID
            LEFT JOIN Users u ON u.UserID = d.CreatedBy
            ORDER BY d.DeliveryDate DESC, d.DeliveryID DESC
            LIMIT %s
            """,
            (limit,),
        )

    @staticmethod
    def get_delivery_lines(delivery_id: int):
        return db.fetch_all(
            """
            SELECT l.LineID, l.ProductID, p.ProductName, p.Barcode,
                   l.QuantityReceived, l.UnitCost
            FROM SupplierDeliveryLines l
            JOIN Products p ON p.ProductID = l.ProductID
            WHERE l.DeliveryID = %s
            ORDER BY l.LineID
            """,
            (delivery_id,),
        )

    @staticmethod
    def record_delivery(
        supplier_id: int,
        delivery_date: date,
        reference_code: str | None,
        notes: str | None,
        created_by: int | None,
        lines: list[dict[str, Any]],
    ) -> int:
        """
        Insert delivery + lines and increase Stock.QuantityAvailable per line.
        Each line: product_id, quantity_received, unit_cost (optional).
        """
        if not lines:
            raise ValueError("Add at least one line item.")

        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO SupplierDeliveries (SupplierID, DeliveryDate, ReferenceCode, Notes, CreatedBy)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING DeliveryID
                """,
                (
                    supplier_id,
                    delivery_date,
                    (reference_code or "").strip() or None,
                    (notes or "").strip() or None,
                    created_by,
                ),
            )
            row = cur.fetchone()
            delivery_id = row[0]

            for line in lines:
                pid = int(line["product_id"])
                qty = int(line["quantity_received"])
                if qty <= 0:
                    raise ValueError("Quantity must be positive.")
                cur.execute("SELECT SupplierID FROM Products WHERE ProductID = %s", (pid,))
                prow = cur.fetchone()
                if not prow or prow[0] != supplier_id:
                    raise ValueError(f"Product {pid} does not belong to the selected supplier.")

                uc = line.get("unit_cost")
                uc_val = float(uc) if uc is not None and uc != "" else None

                cur.execute(
                    """
                    INSERT INTO SupplierDeliveryLines (DeliveryID, ProductID, QuantityReceived, UnitCost)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (delivery_id, pid, qty, uc_val),
                )

                cur.execute("SELECT StockID, QuantityAvailable FROM Stock WHERE ProductID = %s", (pid,))
                st = cur.fetchone()
                if st:
                    cur.execute(
                        "UPDATE Stock SET QuantityAvailable = QuantityAvailable + %s WHERE ProductID = %s",
                        (qty, pid),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO Stock (ProductID, QuantityAvailable, ReorderLevel)
                        VALUES (%s, %s, 10)
                        """,
                        (pid, qty),
                    )

            conn.commit()
            return delivery_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def list_invoices(limit: int = 300):
        return db.fetch_all(
            """
            SELECT i.InvoiceID, i.SupplierID, s.SupplierName, i.InvoiceNumber, i.InvoiceDate,
                   i.DueDate, i.Amount, i.Status, i.PaidDate, i.Notes, i.DeliveryID, i.CreatedAt
            FROM SupplierInvoices i
            JOIN Suppliers s ON s.SupplierID = i.SupplierID
            ORDER BY i.InvoiceDate DESC, i.InvoiceID DESC
            LIMIT %s
            """,
            (limit,),
        )

    @staticmethod
    def add_invoice(
        supplier_id: int,
        invoice_number: str,
        invoice_date: date,
        due_date: date | None,
        amount: Decimal | float,
        status: str,
        notes: str | None,
        delivery_id: int | None,
    ) -> int:
        paid_date = date.today() if status == "paid" else None
        return db.execute_query(
            """
            INSERT INTO SupplierInvoices
                (SupplierID, InvoiceNumber, InvoiceDate, DueDate, Amount, Status, Notes, DeliveryID, PaidDate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING InvoiceID
            """,
            (
                supplier_id,
                invoice_number.strip(),
                invoice_date,
                due_date,
                float(amount),
                status,
                (notes or "").strip() or None,
                delivery_id,
                paid_date,
            ),
            fetch_id=True,
        )

    @staticmethod
    def update_invoice_status(invoice_id: int, status: str):
        if status == "paid":
            db.execute_query(
                """
                UPDATE SupplierInvoices
                SET Status = %s, PaidDate = COALESCE(PaidDate, CURRENT_DATE)
                WHERE InvoiceID = %s
                """,
                (status, invoice_id),
            )
        elif status == "pending":
            db.execute_query(
                """
                UPDATE SupplierInvoices SET Status = %s, PaidDate = NULL WHERE InvoiceID = %s
                """,
                (status, invoice_id),
            )
        else:
            db.execute_query(
                "UPDATE SupplierInvoices SET Status = %s, PaidDate = NULL WHERE InvoiceID = %s",
                (status, invoice_id),
            )

    @staticmethod
    def get_low_stock_items_for_supplier(supplier_id: int):
        return db.fetch_all(
            """
            SELECT p.ProductID, p.ProductName, p.Barcode,
                   s.QuantityAvailable, s.ReorderLevel
            FROM Products p
            JOIN Stock s ON s.ProductID = p.ProductID
            WHERE p.SupplierID = %s
              AND s.QuantityAvailable <= s.ReorderLevel
            ORDER BY s.QuantityAvailable ASC, p.ProductName
            """,
            (supplier_id,),
        )

    @staticmethod
    def list_deliveries_for_supplier(supplier_id: int, limit: int = 50):
        return db.fetch_all(
            """
            SELECT DeliveryID, DeliveryDate, ReferenceCode, Notes, CreatedAt
            FROM SupplierDeliveries
            WHERE SupplierID = %s
            ORDER BY DeliveryDate DESC, DeliveryID DESC
            LIMIT %s
            """,
            (supplier_id, limit),
        )

    @staticmethod
    def format_restock_email(supplier_id: int) -> tuple[str, str, str | None]:
        """Build subject and body from templates + low-stock lines; returns (subject, body, supplier_email)."""
        sup = db.fetch_one(
            "SELECT SupplierName, Email FROM Suppliers WHERE SupplierID = %s",
            (supplier_id,),
        )
        if not sup:
            raise ValueError("Supplier not found.")
        store_name = StoreSettings.get_value(STORE_DISPLAY_KEY) or "Retail Supermarket"
        sub_t = (
            StoreSettings.get_value(RESTOCK_SUBJECT_KEY)
            or "Restock request — {store_name} (low stock)"
        )
        body_t = (
            StoreSettings.get_value(RESTOCK_BODY_KEY)
            or (
                "Dear {supplier_name},\n\n"
                "Please arrange supply for the following items:\n\n{items_table}\n\n"
                "Regards,\n{store_name}"
            )
        )
        rows = SupplierLogistics.get_low_stock_items_for_supplier(supplier_id)
        if not rows:
            items_table = "(No items are currently at or below reorder level for this supplier.)"
        else:
            lines = []
            for r in rows:
                lines.append(
                    f"  • {r['productname']} — on hand: {r['quantityavailable']} | "
                    f"reorder at: {r['reorderlevel']} | barcode: {r['barcode']}"
                )
            items_table = "\n".join(lines)
        supplier_name = sup["suppliername"]
        email = (sup.get("email") or "").strip() or None
        ctx = {
            "store_name": store_name,
            "supplier_name": supplier_name,
            "items_table": items_table,
        }
        subject = sub_t.format(**ctx)
        body = body_t.format(**ctx)
        return subject, body, email
