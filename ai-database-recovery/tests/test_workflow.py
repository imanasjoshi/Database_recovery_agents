from app.workflows.recovery_graph import WorkflowManager
from app.core.config import settings

def test_missing_table_workflow():
    settings.DEMO_MODE = True
    workflow = WorkflowManager()
    
    workflow.monitor.simulated_failure = "missing_table"
    workflow.tick()
    workflow.monitor.simulated_failure = None
    
    for _ in range(15):
        state = workflow.tick()
        if state.current_status == "HEALTHY":
            break
            
    assert state.current_status == "HEALTHY"
    assert state.successful_recoveries == 1
    assert state.recovery_attempts >= 1

def test_unknown_escalation():
    settings.DEMO_MODE = True
    workflow = WorkflowManager()
    
    workflow.monitor.simulated_failure = "unknown_critical_failure"
    workflow.tick()
    workflow.monitor.simulated_failure = None
    
    for _ in range(10):
        state = workflow.tick()
        if state.current_status == "AWAITING_APPROVAL":
            break
            
    assert state.current_status == "AWAITING_APPROVAL"
    # Reject it to escalate
    workflow.coordinator.reject_recovery(state.current_incident_id)
    
    assert workflow.coordinator.state.current_status == "ESCALATED"
