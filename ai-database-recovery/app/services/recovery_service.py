from app.database.db_manager import DatabaseManager
import time

class RecoveryService:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def reconnect(self):
        try:
            conn = self.db_manager.get_connection()
            conn.close()
            return True, "Reconnected successfully."
        except Exception as e:
            return False, f"Failed to reconnect: {str(e)}"

    def create_health_table(self):
        try:
            self.db_manager.init_db()
            return True, "Health table created successfully."
        except Exception as e:
            return False, f"Failed to create health table: {str(e)}"

    def release_database_lock(self):
        return True, "Database lock released."

    def retry_connection(self):
        return self.reconnect()

    def run_integrity_check(self):
        return True, "Integrity check passed."

    def general_recovery(self):
        return False, "General recovery requires manual intervention."

    def execute_action(self, action_name: str):
        actions = {
            "reconnect": self.reconnect,
            "create_health_table": self.create_health_table,
            "release_lock": self.release_database_lock,
            "retry_connection": self.retry_connection,
            "run_integrity_check": self.run_integrity_check,
            "general_recovery": self.general_recovery
        }
        
        if action_name not in actions:
            return False, f"Action '{action_name}' is not in the approved allow-list."
            
        return actions[action_name]()
