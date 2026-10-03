from app.agents.base_agent import BaseAgent
from app.core.state import SystemState
from app.database.incident_repository import IncidentRepository
from app.core.config import settings
import datetime

class CoordinatorAgent(BaseAgent):
    def __init__(self, message_bus):
        super().__init__("Coordinator", message_bus)
        self.state = SystemState()
        self.repo = IncidentRepository()
        self.active_incidents = {} # correlation_id -> state
        
    def process_messages(self):
        messages = self.get_messages()
        for msg in messages:
            if msg.message_type == "failure_alert":
                if self.state.current_status == "HEALTHY":
                    self.state.current_status = "FAILED"
                    self.state.current_incident_id = msg.correlation_id
                    self.state.failure_count += 1
                    
                    self.active_incidents[msg.correlation_id] = {
                        "started_at": datetime.datetime.now(),
                        "error": msg.data.get("error"),
                        "attempts": 0,
                        "status": "FAILED"
                    }
                    
                    self.repo.create_incident(
                        incident_id=msg.correlation_id,
                        failure_type="unknown",
                        raw_error=msg.data.get("error")
                    )
                    
            elif msg.message_type == "diagnosis_complete":
                if msg.correlation_id in self.active_incidents:
                    data = msg.data
                    result = data.get("result", {})
                    
                    self.repo.update_incident(
                        msg.correlation_id,
                        failure_type=result.get("failure_type"),
                        diagnosis_source=data.get("source"),
                        root_cause=result.get("root_cause"),
                        recommended_action=result.get("recommended_action"),
                        risk_level=result.get("risk_level"),
                        llm_latency_seconds=data.get("latency"),
                        llm_used=data.get("source") == "OpenAI"
                    )
                    
                    inc = self.active_incidents[msg.correlation_id]
                    inc["action"] = result.get("recommended_action")
                    inc["risk"] = result.get("risk_level")
                    
                    if result.get("risk_level") == "HIGH":
                        self.state.current_status = "AWAITING_APPROVAL"
                        self.repo.update_incident(msg.correlation_id, final_status="AWAITING_APPROVAL")
                    else:
                        self.trigger_recovery(msg.correlation_id)
                        
            elif msg.message_type == "recovery_complete":
                inc = self.active_incidents.get(msg.correlation_id)
                if inc:
                    if msg.data.get("success"):
                        self.state.current_status = "VALIDATING"
                        self.repo.update_incident(msg.correlation_id, recovery_success=True)
                        self.send_message(
                            receiver="ValidationAgent",
                            message_type="validate_recovery",
                            data={},
                            correlation_id=msg.correlation_id
                        )
                    else:
                        self.handle_failure(msg.correlation_id, "recovery failed")
                        
            elif msg.message_type == "validation_complete":
                inc = self.active_incidents.get(msg.correlation_id)
                if inc:
                    if msg.data.get("overall_success"):
                        self.repo.update_incident(msg.correlation_id, validation_success=True)
                        # Expect monitor to confirm next
                    else:
                        self.handle_failure(msg.correlation_id, "validation failed")
                        
            elif msg.message_type in ["confirmed", "confirmation_failed"]:
                inc = self.active_incidents.get(msg.correlation_id)
                if inc:
                    if msg.message_type == "confirmed":
                        self.resolve_incident(msg.correlation_id)
                    else:
                        self.handle_failure(msg.correlation_id, "confirmation failed")
                        
    def trigger_recovery(self, correlation_id: str):
        inc = self.active_incidents.get(correlation_id)
        if inc:
            inc["attempts"] += 1
            self.state.recovery_attempts += 1
            self.state.current_status = "RECOVERING"
            
            self.repo.update_incident(
                correlation_id, 
                recovery_attempts=inc["attempts"],
                recovery_action=inc["action"],
                final_status="RECOVERING"
            )
            
            self.send_message(
                receiver="RecoveryAgent",
                message_type="recover_request",
                data={"action": inc["action"], "attempt": inc["attempts"]},
                correlation_id=correlation_id
            )
            
    def handle_failure(self, correlation_id: str, reason: str):
        inc = self.active_incidents.get(correlation_id)
        if inc:
            if inc["attempts"] >= settings.MAX_RECOVERY_ATTEMPTS:
                self.escalate_incident(correlation_id)
            else:
                self.trigger_recovery(correlation_id)
                
    def escalate_incident(self, correlation_id: str):
        self.state.current_status = "ESCALATED"
        self.state.failed_recoveries += 1
        self.repo.update_incident(
            correlation_id, 
            final_status="ESCALATED",
            resolved_at=datetime.datetime.now()
        )
        if correlation_id in self.active_incidents:
            del self.active_incidents[correlation_id]
            
    def resolve_incident(self, correlation_id: str):
        self.state.current_status = "HEALTHY"
        self.state.successful_recoveries += 1
        
        inc = self.active_incidents.get(correlation_id)
        duration = None
        if inc:
            duration = (datetime.datetime.now() - inc["started_at"]).total_seconds()
            
        self.repo.update_incident(
            correlation_id, 
            final_status="HEALTHY",
            resolved_at=datetime.datetime.now(),
            recovery_duration_seconds=duration
        )
        if correlation_id in self.active_incidents:
            del self.active_incidents[correlation_id]
            
    def approve_recovery(self, correlation_id: str):
        if self.state.current_status == "AWAITING_APPROVAL" and correlation_id in self.active_incidents:
            self.trigger_recovery(correlation_id)
            return True
        return False
        
    def reject_recovery(self, correlation_id: str):
        if self.state.current_status == "AWAITING_APPROVAL" and correlation_id in self.active_incidents:
            self.escalate_incident(correlation_id)
            return True
        return False
