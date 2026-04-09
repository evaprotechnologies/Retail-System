import os

import psycopg2
import psycopg2.extras
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


class DatabaseConnection:
    """Handles secure database connections and common query helpers."""

    def __init__(self):
        self.host = self._get_setting("DB_HOST", "localhost")
        self.database = self._get_setting("DB_NAME", "retailsystemdb")
        self.user = self._get_setting("DB_USER", "postgres")
        self.password = self._get_setting("DB_PASSWORD", "postgres")
        self.port = self._get_setting("DB_PORT", "5432")

    @staticmethod
    def _get_setting(key, default):
        """Read from Streamlit secrets if available, otherwise env/default."""
        try:
            return st.secrets.get(key, os.getenv(key, default))
        except (StreamlitSecretNotFoundError, FileNotFoundError, KeyError):
            return os.getenv(key, default)

    def get_connection(self):
        return psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password,
            port=self.port,
        )

    def fetch_all(self, query, params=None):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()

    def fetch_one(self, query, params=None):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()

    def execute_query(self, query, params=None, fetch_id=False):
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if fetch_id:
                    result = cursor.fetchone()
                    conn.commit()
                    return result[0] if result else None
                conn.commit()
                return None

