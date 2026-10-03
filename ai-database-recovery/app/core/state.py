from pydantic import BaseModel
from typing import Optional, List

class SystemState(BaseModel):
    current_status: str = "HEALTHY"  # HEALTHY, DEGRADED, FAILED, RECOVERING, VALIDATING, ESCALATED, AWAITING_APPROVAL
    database_connected: bool = True
    last_health_check: Optional[str] = None
    failure_count: int = 0
    recovery_attempts: int = 0
    successful_recoveries: int = 0
    failed_recoveries: int = 0
    alerts: List[str] = []
    current_incident_id: Optional[str] = None
    
    # Context for current incident
    failure_type: Optional[str] = None
    recommended_action: Optional[str] = None
    risk_level: Optional[str] = None
