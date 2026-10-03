from app.agents.base_agent import BaseAgent
from app.database.db_manager import DatabaseManager
import uuid

class MonitorAgent(BaseAgent):
    def __init__(self, message_bus):
        super().__init__("DatabaseMonitor", message_bus)
        self.db_manager = DatabaseManager()
        self.simulated_failure = None
        
    def check_health(self):
        if self.simulated_failure:
            if self.simulated_failure == "connection_timeout":
                return False, "connection timeout"
            elif self.simulated_failure == "database_locked":
                return False, "database is locked"
            elif self.simulated_failure == "missing_table":
                return False, "no such table: health_check"
            elif self.simulated_failure == "permission_error":
                return False, "permission denied"
            else:
                return False, f"unknown error: {self.simulated_failure}"
            
        try:
            is_healthy = self.db_manager.check_health()
            if is_healthy:
                return True, "OK"
            else:
                return False, "no such table: health_check"
        except Exception as e:
            return False, str(e)
            
    def run_cycle(self):
        is_healthy, msg = self.check_health()
        
        if not is_healthy:
            incident_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
            self.send_message(
                receiver="Coordinator",
                message_type="failure_alert",
                data={"error": msg},
                correlation_id=incident_id
            )
            self.send_message(
                receiver="DiagnosticsAgent",
                message_type="failure_alert",
                data={"error": msg},
                correlation_id=incident_id
            )
            return incident_id
        return None
        
    def confirm_health(self, correlation_id: str):
        is_healthy, _ = self.check_health()
        self.send_message(
            receiver="Coordinator",
            message_type="confirmed" if is_healthy else "confirmation_failed",
            data={"healthy": is_healthy},
            correlation_id=correlation_id
        )
        return is_healthy
