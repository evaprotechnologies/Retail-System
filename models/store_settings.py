from models.database import DatabaseConnection

db = DatabaseConnection()

CART_REMOVAL_PIN_KEY = "cart_removal_pin"


class StoreSettings:
    """Key/value store settings (e.g. store-level cart removal PIN)."""

    @staticmethod
    def get_value(key: str):
        row = db.fetch_one(
            "SELECT SettingValue FROM StoreSettings WHERE SettingKey = %s",
            (key,),
        )
        return row["settingvalue"] if row else None

    @staticmethod
    def verify_cart_removal_pin(pin: str) -> bool:
        if not pin:
            return False
        stored = StoreSettings.get_value(CART_REMOVAL_PIN_KEY)
        return stored is not None and pin.strip() == stored

    @staticmethod
    def update_cart_removal_pin(new_pin: str):
        db.execute_query(
            """
            INSERT INTO StoreSettings (SettingKey, SettingValue)
            VALUES (%s, %s)
            ON CONFLICT (SettingKey) DO UPDATE SET SettingValue = EXCLUDED.SettingValue
            """,
            (CART_REMOVAL_PIN_KEY, new_pin.strip()),
        )
