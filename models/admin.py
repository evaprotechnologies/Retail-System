from models.database import DatabaseConnection

db = DatabaseConnection()


class StaffAdmin:
    """Manager-facing user and sales audit operations."""

    @staticmethod
    def list_users():
        return db.fetch_all(
            """
            SELECT UserID, Username, FullName, Role, IsActive, CreatedAt, LastLogin
            FROM Users
            ORDER BY Role, Username
            """
        )

    @staticmethod
    def list_cashiers():
        return db.fetch_all(
            """
            SELECT UserID, Username, FullName, IsActive, CreatedAt, LastLogin
            FROM Users
            WHERE Role = 'cashier'
            ORDER BY Username
            """
        )

    @staticmethod
    def add_user(username, password, full_name, role):
        db.execute_query(
            """
            INSERT INTO Users (Username, Password, FullName, Role, IsActive)
            VALUES (%s, %s, %s, %s, TRUE)
            """,
            (username, password, full_name, role),
        )

    @staticmethod
    def set_user_active(user_id: int, is_active: bool):
        db.execute_query(
            "UPDATE Users SET IsActive = %s WHERE UserID = %s",
            (is_active, user_id),
        )

    @staticmethod
    def get_cashier_sales(user_id: int):
        return db.fetch_all(
            """
            SELECT SaleID, SaleDate, TotalAmount, PaymentMethod, ProcessedBy
            FROM Sales
            WHERE ProcessedBy = %s
            ORDER BY SaleDate DESC
            """,
            (user_id,),
        )

    @staticmethod
    def get_sale_details(sale_id: int):
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
