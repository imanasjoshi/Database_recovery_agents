from app.agents.base_agent import BaseAgent
from app.services.diagnostic_service import DiagnosticService

class DiagnosticsAgent(BaseAgent):
    def __init__(self, message_bus):
        super().__init__("DiagnosticsAgent", message_bus)
        self.diagnostic_service = DiagnosticService()
        
    def process_messages(self):
        messages = self.get_messages()
        for msg in messages:
            if msg.message_type == "failure_alert":
                error_msg = msg.data.get("error", "")
                diagnosis = self.diagnostic_service.diagnose(error_msg)
                
                self.send_message(
                    receiver="Coordinator",
                    message_type="diagnosis_complete",
                    data=diagnosis,
                    correlation_id=msg.correlation_id
                )
