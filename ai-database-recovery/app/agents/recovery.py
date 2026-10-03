from app.agents.base_agent import BaseAgent
from app.services.recovery_service import RecoveryService
import time

class RecoveryAgent(BaseAgent):
    def __init__(self, message_bus):
        super().__init__("RecoveryAgent", message_bus)
        self.recovery_service = RecoveryService()
        
    def process_messages(self):
        messages = self.get_messages()
        for msg in messages:
            if msg.message_type == "recover_request":
                action = msg.data.get("action")
                attempt = msg.data.get("attempt", 1)
                
                # simulate exponential backoff if attempt > 1
                if attempt > 1:
                    time.sleep(2 ** (attempt - 2))
                
                success, result_msg = self.recovery_service.execute_action(action)
                
                self.send_message(
                    receiver="Coordinator",
                    message_type="recovery_complete",
                    data={"success": success, "message": result_msg},
                    correlation_id=msg.correlation_id
                )
