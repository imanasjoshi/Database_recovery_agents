from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.workflows.recovery_graph import WorkflowManager
from app.database.incident_repository import IncidentRepository
from app.database.failure_simulator import FailureSimulator
import threading
import time

router = APIRouter()
workflow = WorkflowManager()
repo = IncidentRepository()
simulator = FailureSimulator()

monitor_thread = None
monitor_running = False

def monitor_loop():
    global monitor_running
    while monitor_running:
        workflow.tick()
        time.sleep(1)

@router.get("/health")
def health_check():
    return {"status": "ok"}
    
@router.get("/status")
def get_status():
    return workflow.coordinator.state.model_dump()
    
@router.post("/monitor/start")
def start_monitor():
    global monitor_thread, monitor_running
    if not monitor_running:
        monitor_running = True
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        return {"status": "started"}
    return {"status": "already running"}
    
@router.post("/monitor/stop")
def stop_monitor():
    global monitor_running
    monitor_running = False
    return {"status": "stopped"}

class SimulateRequest(BaseModel):
    failure_type: str
    
@router.post("/incidents/simulate")
def simulate_incident(req: SimulateRequest):
    try:
        msg = simulator.simulate(req.failure_type)
        workflow.monitor.simulated_failure = req.failure_type
        # Give it a tick to detect
        workflow.tick()
        workflow.monitor.simulated_failure = None # clear after detection
        return {"status": "simulated", "message": msg}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
@router.get("/incidents")
def get_incidents():
    return repo.get_all_incidents()
    
@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    inc = repo.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc

@router.get("/messages")
def get_messages():
    return repo.get_messages()
    
@router.post("/recovery/{incident_id}/approve")
def approve_recovery(incident_id: str):
    success = workflow.coordinator.approve_recovery(incident_id)
    if success:
        return {"status": "approved"}
    raise HTTPException(status_code=400, detail="Cannot approve this incident")
    
@router.post("/recovery/{incident_id}/reject")
def reject_recovery(incident_id: str):
    success = workflow.coordinator.reject_recovery(incident_id)
    if success:
        return {"status": "rejected"}
    raise HTTPException(status_code=400, detail="Cannot reject this incident")
