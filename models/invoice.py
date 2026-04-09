"""Customer tax invoice / receipt as PDF (generated from Sales + Sales_Details)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fpdf import FPDF

from models.database import DatabaseConnection

db = DatabaseConnection()

STORE_NAME = "Retail Supermarket"
STORE_ADDRESS = "Customer copy — thank you for your purchase"


def _safe_pdf_text(value: Any) -> str:
    """Keep Helvetica-safe single-line text."""
    if value is None:
        return ""
    s = str(value).replace("\r", " ").replace("\n", " ")
    return "".join(c if 32 <= ord(c) < 127 or c in " " else "?" for c in s)


class InvoiceService:
    @staticmethod
    def get_sale_header(sale_id: int):
        return db.fetch_one(
            """
            SELECT s.SaleID, s.SaleDate, s.TotalAmount, s.PaymentMethod, s.ProcessedBy,
                   COALESCE(u.FullName, '') AS CashierName
            FROM Sales s
            LEFT JOIN Users u ON u.UserID = s.ProcessedBy
            WHERE s.SaleID = %s
            """,
            (sale_id,),
        )

    @staticmethod
    def get_sale_lines(sale_id: int):
        return db.fetch_all(
            """
            SELECT p.ProductName, p.Barcode, sd.QuantitySold, sd.UnitPrice, sd.LineTotal
            FROM Sales_Details sd
            JOIN Products p ON p.ProductID = sd.ProductID
            WHERE sd.SaleID = %s
            ORDER BY sd.SaleDetailID
            """,
            (sale_id,),
        )

    @staticmethod
    def user_can_view_sale(user, header: dict | None) -> bool:
        if not header:
            return False
        if str(user.role).lower() == "manager":
            return True
        pb = header.get("processedby")
        if pb is None:
            return False
        return int(pb) == int(user.user_id)

    @staticmethod
    def format_receipt_text(sale_id: int) -> str:
        header = InvoiceService.get_sale_header(sale_id)
        if not header:
            return "Sale not found."
        lines = InvoiceService.get_sale_lines(sale_id)
        sd = header["saledate"]
        if isinstance(sd, datetime):
            sd_str = sd.strftime("%Y-%m-%d %H:%M")
        else:
            sd_str = str(sd)
        parts = [
            "=" * 48,
            STORE_NAME.center(48),
            "TAX INVOICE / CUSTOMER RECEIPT".center(48),
            "=" * 48,
            f"Invoice #: {header['saleid']}",
            f"Date:      {sd_str}",
            f"Payment:   {header['paymentmethod']}",
            f"Served by: {_safe_pdf_text(header.get('cashiername'))}",
            "-" * 48,
            f"{'Item':<24} {'Qty':>4} {'Unit':>8} {'Total':>8}",
            "-" * 48,
        ]
        for row in lines:
            name = _safe_pdf_text(row["productname"])[:24]
            parts.append(
                f"{name:<24} {int(row['quantitysold']):>4} "
                f"{float(row['unitprice']):>8.2f} {float(row['linetotal']):>8.2f}"
            )
            bc = row.get("barcode")
            if bc:
                parts.append(f"  Barcode: {_safe_pdf_text(bc)}")
        parts.extend(
            [
                "-" * 48,
                f"{'TOTAL (ZMW)':<36}{float(header['totalamount']):>12.2f}",
                "=" * 48,
                STORE_ADDRESS,
                "Retain this document for your records.",
                "=" * 48,
            ]
        )
        return "\n".join(parts)

    @staticmethod
    def build_invoice_pdf_bytes(sale_id: int) -> bytes:
        header = InvoiceService.get_sale_header(sale_id)
        if not header:
            raise ValueError("Sale not found")
        lines = InvoiceService.get_sale_lines(sale_id)

        pdf = FPDF(format="A4", unit="mm")
        pdf.set_auto_page_break(auto=True, margin=14)
        pdf.set_margins(14, 14, 14)
        pdf.add_page()

        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, _safe_pdf_text(STORE_NAME), ln=1, align="C")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, "Tax invoice / Customer receipt", ln=1, align="C")
        pdf.ln(4)

        pdf.set_font("Helvetica", "", 10)
        sd = header["saledate"]
        if isinstance(sd, datetime):
            sd_str = sd.strftime("%Y-%m-%d %H:%M")
        else:
            sd_str = str(sd)

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(40, 6, "Invoice #:", ln=0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, str(header["saleid"]), ln=1)

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(40, 6, "Date:", ln=0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, _safe_pdf_text(sd_str), ln=1)

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(40, 6, "Payment:", ln=0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, _safe_pdf_text(header["paymentmethod"]), ln=1)

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(40, 6, "Cashier:", ln=0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, _safe_pdf_text(header.get("cashiername")), ln=1)

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(85, 7, "Item", border="B", ln=0)
        pdf.cell(15, 7, "Qty", border="B", ln=0, align="R")
        pdf.cell(30, 7, "Unit ZMW", border="B", ln=0, align="R")
        pdf.cell(30, 7, "Line ZMW", border="B", ln=1, align="R")

        pdf.set_font("Helvetica", "", 9)
        for row in lines:
            name = _safe_pdf_text(row["productname"])
            qty = int(row["quantitysold"])
            unit = float(row["unitprice"])
            lt = float(row["linetotal"])
            barcode = row.get("barcode")

            pdf.cell(85, 6, name[:55], ln=0)
            pdf.cell(15, 6, str(qty), ln=0, align="R")
            pdf.cell(30, 6, f"{unit:.2f}", ln=0, align="R")
            pdf.cell(30, 6, f"{lt:.2f}", ln=1, align="R")
            if barcode:
                pdf.set_font("Helvetica", "I", 8)
                pdf.cell(0, 4, f"  Barcode: {_safe_pdf_text(barcode)}", ln=1)
                pdf.set_font("Helvetica", "", 9)

        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(130, 8, "Total (ZMW)", ln=0, align="R")
        pdf.cell(30, 8, f"{float(header['totalamount']):.2f}", ln=1, align="R")

        pdf.ln(6)
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(0, 5, _safe_pdf_text(STORE_ADDRESS) + "\nRetain for warranty, returns, and audit.")

        raw = pdf.output(dest="S")
        if isinstance(raw, str):
            return raw.encode("latin-1", errors="replace")
        return bytes(raw)

    @staticmethod
    def get_pdf_for_user(sale_id: int, user) -> bytes:
        header = InvoiceService.get_sale_header(sale_id)
        if not InvoiceService.user_can_view_sale(user, header):
            raise PermissionError("You cannot access this invoice.")
        return InvoiceService.build_invoice_pdf_bytes(sale_id)
