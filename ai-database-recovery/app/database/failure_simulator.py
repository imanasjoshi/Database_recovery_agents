import sqlite3
from app.core.config import settings

class FailureSimulator:
    def __init__(self):
        self.db_path = settings.DATABASE_PATH
        
    def simulate(self, failure_type: str):
        if not settings.DEMO_MODE:
            raise Exception("Cannot simulate failures outside of demo mode")
            
        if failure_type == "connection_timeout":
            # We simulate this at the monitor level rather than actually locking the DB
            return "Simulated connection timeout"
            
        elif failure_type == "missing_table":
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS health_check")
                conn.commit()
            return "health_check table dropped"
            
        elif failure_type == "database_locked":
            return "Simulated database lock"
            
        elif failure_type == "permission_error":
            return "Simulated permission error"
            
        else:
            return "Unknown failure type"
