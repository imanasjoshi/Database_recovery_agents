from app.core.message_bus import MessageBus
from app.agents.monitor import MonitorAgent
from app.agents.diagnostics import DiagnosticsAgent
from app.agents.coordinator import CoordinatorAgent
from app.agents.recovery import RecoveryAgent
from app.agents.validation import ValidationAgent

class WorkflowManager:
    def __init__(self):
        self.message_bus = MessageBus()
        self.coordinator = CoordinatorAgent(self.message_bus)
        self.monitor = MonitorAgent(self.message_bus)
        self.diagnostics = DiagnosticsAgent(self.message_bus)
        self.recovery = RecoveryAgent(self.message_bus)
        self.validation = ValidationAgent(self.message_bus)
        
    def tick(self):
        """Executes one cycle of the agents."""
        # 1. Monitor checks health
        if self.coordinator.state.current_status == "HEALTHY":
            incident_id = self.monitor.run_cycle()
            
        # 2. Coordinator processes alerts
        self.coordinator.process_messages()
        
        # 3. Diagnostics processes (if FAILED)
        self.diagnostics.process_messages()
        
        # 4. Coordinator processes diagnosis
        self.coordinator.process_messages()
        
        # 5. Recovery processes (if RECOVERING)
        self.recovery.process_messages()
        
        # 6. Coordinator processes recovery completion
        self.coordinator.process_messages()
        
        # 7. Validation processes (if VALIDATING)
        self.validation.process_messages()
        
        # 8. Coordinator processes validation completion
        self.coordinator.process_messages()
        
        # 9. Monitor confirms health
        if self.coordinator.state.current_status == "VALIDATING" or any(m.message_type == "validation_complete" for m in self.message_bus.history[-5:]):
             incident_id = self.coordinator.state.current_incident_id
             if incident_id:
                 self.monitor.confirm_health(incident_id)
                 
        # 10. Coordinator processes confirmation
        self.coordinator.process_messages()
        
        return self.coordinator.state
