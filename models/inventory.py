from models.database import DatabaseConnection

db = DatabaseConnection()


class POSSystem:
    """Encapsulates POS operations and inventory queries."""

    @staticmethod
    def get_products_for_sale():
        query = """
            SELECT p.ProductID, p.ProductName, p.Barcode, p.SellingPrice, COALESCE(s.QuantityAvailable, 0) AS Stock
            FROM Products p
            LEFT JOIN Stock s ON p.ProductID = s.ProductID
            WHERE COALESCE(s.QuantityAvailable, 0) > 0
            ORDER BY p.ProductName
        """
        return db.fetch_all(query)

    @staticmethod
    def get_product_by_id(product_id):
        query = """
            SELECT p.ProductID, p.ProductName, p.SellingPrice, COALESCE(s.QuantityAvailable, 0) AS QuantityAvailable
            FROM Products p
            LEFT JOIN Stock s ON p.ProductID = s.ProductID
            WHERE p.ProductID = %s
        """
        return db.fetch_one(query, (product_id,))

    @staticmethod
    def get_product_by_barcode(barcode: str):
        if not barcode or not str(barcode).strip():
            return None
        code = str(barcode).strip()
        query = """
            SELECT p.ProductID, p.ProductName, p.Barcode, p.SellingPrice, COALESCE(s.QuantityAvailable, 0) AS QuantityAvailable
            FROM Products p
            LEFT JOIN Stock s ON p.ProductID = s.ProductID
            WHERE p.Barcode = %s
        """
        return db.fetch_one(query, (code,))

    @staticmethod
    def get_low_stock():
        query = """
            SELECT p.ProductName, s.QuantityAvailable, s.ReorderLevel
            FROM Stock s JOIN Products p ON s.ProductID = p.ProductID
            WHERE s.QuantityAvailable <= s.ReorderLevel
        """
        return db.fetch_all(query)

    @staticmethod
    def get_full_catalog():
        query = """
            SELECT p.ProductID, p.ProductName, p.Barcode, p.SellingPrice, s.QuantityAvailable
            FROM Products p LEFT JOIN Stock s ON p.ProductID = s.ProductID
        """
        return db.fetch_all(query)

    @staticmethod
    def get_sales_summary():
        query = "SELECT * FROM View_DailySales_Summary ORDER BY TransactionDate DESC"
        return db.fetch_all(query)

    @staticmethod
    def get_products():
        query = "SELECT ProductID, ProductName, Barcode, SellingPrice FROM Products"
        return db.fetch_all(query)

    @staticmethod
    def get_suppliers():
        query = "SELECT SupplierID, SupplierName FROM Suppliers"
        return db.fetch_all(query)

    @staticmethod
    def get_suppliers_detailed():
        query = """
            SELECT SupplierID, SupplierName, ContactPerson, PhoneNumber, Email, CreatedAt
            FROM Suppliers
            ORDER BY SupplierName
        """
        return db.fetch_all(query)

    @staticmethod
    def add_supplier(name, contact_person, phone, email):
        query = """
            INSERT INTO Suppliers (SupplierName, ContactPerson, PhoneNumber, Email)
            VALUES (%s, %s, %s, %s)
            RETURNING SupplierID
        """
        return db.execute_query(query, (name.strip(), contact_person.strip() if contact_person else None,
                                       phone.strip() if phone else None, email.strip() if email else None), fetch_id=True)

    @staticmethod
    def update_supplier(supplier_id, name, contact_person, phone, email):
        query = """
            UPDATE Suppliers
            SET SupplierName = %s, ContactPerson = %s, PhoneNumber = %s, Email = %s
            WHERE SupplierID = %s
        """
        db.execute_query(query, (name.strip(), contact_person.strip() if contact_person else None,
                                phone.strip() if phone else None, email.strip() if email else None, supplier_id))

    @staticmethod
    def delete_supplier(supplier_id):
        # Check if supplier has products
        check_query = "SELECT COUNT(*) as product_count FROM Products WHERE SupplierID = %s"
        result = db.fetch_one(check_query, (supplier_id,))
        if result and result['product_count'] > 0:
            raise ValueError("Cannot delete supplier with existing products. Reassign products first.")

        query = "DELETE FROM Suppliers WHERE SupplierID = %s"
        db.execute_query(query, (supplier_id,))

    @staticmethod
    def get_supplier_products(supplier_id):
        query = """
            SELECT p.ProductID, p.ProductName, p.Category, p.SellingPrice, COALESCE(s.QuantityAvailable, 0) as Stock
            FROM Products p
            LEFT JOIN Stock s ON p.ProductID = s.ProductID
            WHERE p.SupplierID = %s
            ORDER BY p.ProductName
        """
        return db.fetch_all(query, (supplier_id,))

    @staticmethod
    def add_product(name, category, price, supplier_id, stock, barcode: str):
        """Add a new product and its stock."""
        product_query = """
            INSERT INTO Products (ProductName, Category, SellingPrice, SupplierID, Barcode)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING ProductID
        """
        product_id = db.execute_query(
            product_query,
            (name, category, price, supplier_id, barcode.strip()),
            fetch_id=True,
        )
        stock_query = "INSERT INTO Stock (ProductID, QuantityAvailable) VALUES (%s, %s)"
        db.execute_query(stock_query, (product_id, stock))
        return product_id

    @staticmethod
    def update_price(product_id, new_price):
        query = "UPDATE Products SET SellingPrice = %s WHERE ProductID = %s"
        db.execute_query(query, (new_price, product_id))

    @staticmethod
    def delete_product(product_id):
        query = "DELETE FROM Products WHERE ProductID = %s"
        db.execute_query(query, (product_id,))

    @staticmethod
    def process_transaction(cart_items, total_amount, processed_by, payment_method="cash"):
        """Creates sale header and details and returns sale id."""
        sale_query = """
            INSERT INTO Sales (TotalAmount, ProcessedBy, PaymentMethod)
            VALUES (%s, %s, %s)
            RETURNING SaleID
        """
        sale_id = db.execute_query(sale_query, (total_amount, processed_by, payment_method), fetch_id=True)

        detail_query = """
            INSERT INTO Sales_Details (SaleID, ProductID, QuantitySold, UnitPrice, LineTotal)
            VALUES (%s, %s, %s, %s, %s)
        """
        for item in cart_items:
            db.execute_query(
                detail_query,
                (
                    sale_id,
                    item["product_id"],
                    item["quantity"],
                    item["unit_price"],
                    item["line_total"],
                ),
            )

        return sale_id

    @staticmethod
    def get_sales_for_user(user_id: int):
        return db.fetch_all(
            """
            SELECT SaleID, SaleDate, TotalAmount, PaymentMethod
            FROM Sales
            WHERE ProcessedBy = %s
            ORDER BY SaleDate DESC
            """,
            (user_id,),
        )

    @staticmethod
    def get_sale_line_items(sale_id: int):
        return db.fetch_all(
            """
            SELECT sd.SaleDetailID, sd.ProductID, p.ProductName, p.Barcode,
                   sd.QuantitySold, sd.UnitPrice, sd.LineTotal
            FROM Sales_Details sd
            JOIN Products p ON p.ProductID = sd.ProductID
            WHERE sd.SaleID = %s
            ORDER BY sd.SaleDetailID
            """,
            (sale_id,),
        )

    @staticmethod
    def list_recent_sales(limit: int = 500):
        return db.fetch_all(
            """
            SELECT s.SaleID, s.SaleDate, s.TotalAmount, s.PaymentMethod, s.ProcessedBy,
                   COALESCE(u.FullName, '') AS CashierName
            FROM Sales s
            LEFT JOIN Users u ON u.UserID = s.ProcessedBy
            ORDER BY s.SaleDate DESC
            LIMIT %s
            """,
            (limit,),
        )

