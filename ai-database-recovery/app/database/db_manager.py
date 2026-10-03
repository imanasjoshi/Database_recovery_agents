import sqlite3
import os
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_path = settings.DATABASE_PATH
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS health_check (
                        id INTEGER PRIMARY KEY,
                        status TEXT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sample_data (
                        id INTEGER PRIMARY KEY,
                        name TEXT
                    )
                ''')
                # Insert initial health record
                cursor.execute("INSERT OR IGNORE INTO health_check (id, status) VALUES (1, 'OK')")
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize demo database: {e}")

    def check_health(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status FROM health_check LIMIT 1")
                res = cursor.fetchone()
                if res and res[0] == 'OK':
                    return True
        except Exception:
            return False
        return False
