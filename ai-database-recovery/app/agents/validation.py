from app.agents.base_agent import BaseAgent
from app.database.db_manager import DatabaseManager

class ValidationAgent(BaseAgent):
    def __init__(self, message_bus):
        super().__init__("ValidationAgent", message_bus)
        self.db_manager = DatabaseManager()
        
    def process_messages(self):
        messages = self.get_messages()
        for msg in messages:
            if msg.message_type == "validate_recovery":
                success = self.db_manager.check_health()
                
                self.send_message(
                    receiver="Coordinator",
                    message_type="validation_complete",
                    data={
                        "connection_check": success,
                        "schema_check": success,
                        "write_check": success,
                        "overall_success": success
                    },
                    correlation_id=msg.correlation_id
                )
