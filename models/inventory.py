from models.database import DatabaseConnection

db = DatabaseConnection()


class POSSystem:
    """Encapsulates POS operations and inventory queries."""

    @staticmethod
    def get_products_for_sale():
        query = """
            SELECT p.ProductID, p.ProductName, p.SellingPrice, COALESCE(s.QuantityAvailable, 0) AS Stock
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
            SELECT p.ProductID, p.ProductName, p.SellingPrice, s.QuantityAvailable
            FROM Products p LEFT JOIN Stock s ON p.ProductID = s.ProductID
        """
        return db.fetch_all(query)

    @staticmethod
    def get_sales_summary():
        query = "SELECT * FROM View_DailySales_Summary ORDER BY TransactionDate DESC"
        return db.fetch_all(query)

    @staticmethod
    def get_products():
        query = "SELECT ProductID, ProductName, SellingPrice FROM Products"
        return db.fetch_all(query)

    @staticmethod
    def get_suppliers():
        query = "SELECT SupplierID, SupplierName FROM Suppliers"
        return db.fetch_all(query)

    @staticmethod
    def add_product(name, price, supplier_id, stock):
        """Add a new product and its stock."""
        product_query = "INSERT INTO Products (ProductName, SellingPrice, SupplierID) VALUES (%s, %s, %s) RETURNING ProductID"
        product_id = db.execute_query(product_query, (name, price, supplier_id), fetch_id=True)
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

