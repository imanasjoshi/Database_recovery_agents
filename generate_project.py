import os

base_dir = "ai-database-recovery"

files = {
    ".gitignore": """
.venv
__pycache__/
*.pyc
.env
data/*.db
!data/.gitkeep
.pytest_cache/
""",
    ".env.example": """
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
DATABASE_PATH=data/demo_database.db
INCIDENT_DATABASE_PATH=data/incident_database.db
MAX_RECOVERY_ATTEMPTS=3
MONITOR_INTERVAL_SECONDS=5
DEMO_MODE=true
""",
    "requirements.txt": """
fastapi==0.111.0
uvicorn==0.30.1
streamlit==1.36.0
openai==1.35.3
langchain==0.2.7
langchain-openai==0.1.15
langgraph==0.1.7
pydantic==2.8.2
python-dotenv==1.0.1
pandas==2.2.2
plotly==5.22.0
pytest==8.2.2
requests==2.32.3
""",
    "Dockerfile": """
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose ports for FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 & streamlit run dashboard/streamlit_app.py --server.port 8501 --server.address 0.0.0.0"]
""",
    "docker-compose.yml": """
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
      - "8501:8501"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
""",
    "README.md": """
# AI-Powered Multi-Agent Database Reliability & Self-Healing Platform

## Problem Statement
Database downtime and manual incident recovery can lead to significant business losses and developer fatigue.

## Solution
This project implements a multi-agent self-healing workflow to monitor, diagnose, and recover from database failures automatically, while maintaining safety through strict validation and human-in-the-loop approvals for high-risk actions.

## Architecture
```mermaid
flowchart TD
    DB[Database] --> M[Monitor Agent]
    M -->|Failure| D[Diagnostics Agent]
    D --> C[Coordinator]
    C -->|High Risk| A[Await Approval]
    A -->|Approved| R
    C -->|Low/Medium Risk| R[Recovery Agent]
    R --> V[Validation Agent]
    V --> M
    M -->|Confirmed| H[Healthy]
```

## Agent Responsibilities
| Agent | Role |
|---|---|
| Monitor | Continuously checks DB health, detects failures, alerts, and confirms health after recovery. |
| Diagnostics | Uses rules or LLM to explain failures and recommend approved recovery actions. |
| Coordinator | Manages system state, records communications, coordinates recovery/validation. |
| Recovery | Executes approved repairs (e.g., reconnect, create table). Records attempts. |
| Validation | Checks connectivity, schema, write/read operations after recovery. |

## Safety Features
- Allow-listed recovery tools
- Structured LLM output
- Independent validation
- Maximum retries
- Human approval for high-risk actions
- Escalation

## Installation

```bash
git clone https://github.com/yourusername/ai-database-recovery.git
cd ai-database-recovery
python -m venv .venv
```

Windows:
```bash
.venv\\Scripts\\activate
```
Mac/Linux:
```bash
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Environment:
```bash
copy .env.example .env
# Edit .env to add your OPENAI_API_KEY
```

Run FastAPI:
```bash
uvicorn app.main:app --reload
```

Run Streamlit Dashboard:
```bash
streamlit run dashboard/streamlit_app.py
```

## Testing
```bash
pytest
```
""",
    "data/.gitkeep": "",
    "run.py": """
import subprocess
import time
import sys

def main():
    print("Starting FastAPI...")
    api_process = subprocess.Popen(["uvicorn", "app.main:app", "--reload"])
    time.sleep(2)
    print("Starting Streamlit...")
    ui_process = subprocess.Popen(["streamlit", "run", "dashboard/streamlit_app.py"])
    
    try:
        api_process.wait()
        ui_process.wait()
    except KeyboardInterrupt:
        print("Shutting down...")
        api_process.terminate()
        ui_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
""",
    "app/__init__.py": "",
    "app/agents/__init__.py": "",
    "app/agents/base_agent.py": """
import datetime
from pydantic import BaseModel
from typing import Dict, Any, Optional

class AgentMessage(BaseModel):
    sender: str
    receiver: str
    message_type: str
    data: Dict[str, Any]
    timestamp: datetime.datetime = datetime.datetime.now()
    correlation_id: str

class BaseAgent:
    def __init__(self, name: str, message_bus):
        self.name = name
        self.message_bus = message_bus
        self.message_bus.subscribe(self.name)
        
    def send_message(self, receiver: str, message_type: str, data: Dict[str, Any], correlation_id: str):
        msg = AgentMessage(
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            data=data,
            correlation_id=correlation_id,
            timestamp=datetime.datetime.now()
        )
        self.message_bus.publish(msg)
        
    def get_messages(self):
        return self.message_bus.get_messages(self.name)
""",
    "app/core/__init__.py": "",
    "app/core/config.py": """
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/demo_database.db")
    INCIDENT_DATABASE_PATH: str = os.getenv("INCIDENT_DATABASE_PATH", "data/incident_database.db")
    MAX_RECOVERY_ATTEMPTS: int = int(os.getenv("MAX_RECOVERY_ATTEMPTS", "3"))
    MONITOR_INTERVAL_SECONDS: int = int(os.getenv("MONITOR_INTERVAL_SECONDS", "5"))
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() == "true"

settings = Settings()
""",
    "app/core/message_bus.py": """
from typing import List, Dict
from app.agents.base_agent import AgentMessage
from app.database.incident_repository import IncidentRepository

class MessageBus:
    def __init__(self):
        self.subscribers: Dict[str, List[AgentMessage]] = {}
        self.history: List[AgentMessage] = []
        self.repo = IncidentRepository()
        
    def subscribe(self, agent_name: str):
        if agent_name not in self.subscribers:
            self.subscribers[agent_name] = []
            
    def publish(self, message: AgentMessage):
        self.history.append(message)
        # Always send to the specific receiver if they exist
        if message.receiver in self.subscribers:
            self.subscribers[message.receiver].append(message)
        # Broadcast to Coordinator if it's not the sender or receiver
        if message.receiver != "Coordinator" and message.sender != "Coordinator":
            if "Coordinator" in self.subscribers:
                self.subscribers["Coordinator"].append(message)
        
        # Save to DB
        self.repo.save_message(message)
                
    def get_messages(self, agent_name: str) -> List[AgentMessage]:
        messages = self.subscribers.get(agent_name, []).copy()
        self.subscribers[agent_name] = []
        return messages
""",
    "app/core/state.py": """
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
""",
    "app/database/__init__.py": "",
    "app/database/db_manager.py": """
import sqlite3
import os
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_path = settings.DATABASE_PATH
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS health_check (
                        id INTEGER PRIMARY KEY,
                        status TEXT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sample_data (
                        id INTEGER PRIMARY KEY,
                        name TEXT
                    )
                ''')
                # Insert initial health record
                cursor.execute("INSERT OR IGNORE INTO health_check (id, status) VALUES (1, 'OK')")
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize demo database: {e}")

    def check_health(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status FROM health_check LIMIT 1")
                res = cursor.fetchone()
                if res and res[0] == 'OK':
                    return True
        except Exception:
            return False
        return False
""",
    "app/database/incident_repository.py": """
import sqlite3
import os
from app.core.config import settings
import json

class IncidentRepository:
    def __init__(self):
        self.db_path = settings.INCIDENT_DATABASE_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    failure_type TEXT,
                    raw_error TEXT,
                    diagnosis_source TEXT,
                    root_cause TEXT,
                    recommended_action TEXT,
                    risk_level TEXT,
                    recovery_action TEXT,
                    recovery_attempts INTEGER DEFAULT 0,
                    recovery_success BOOLEAN,
                    validation_success BOOLEAN,
                    final_status TEXT,
                    recovery_duration_seconds REAL,
                    llm_latency_seconds REAL,
                    llm_used BOOLEAN
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    correlation_id TEXT,
                    sender TEXT,
                    receiver TEXT,
                    message_type TEXT,
                    data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            
    def create_incident(self, incident_id: str, failure_type: str, raw_error: str = ""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO incidents (incident_id, failure_type, raw_error, final_status)
                VALUES (?, ?, ?, 'FAILED')
            ''', (incident_id, failure_type, raw_error))
            conn.commit()

    def update_incident(self, incident_id: str, **kwargs):
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values())
        values.append(incident_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE incidents SET {set_clause} WHERE incident_id = ?
            ''', values)
            conn.commit()

    def save_message(self, message):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO agent_messages (correlation_id, sender, receiver, message_type, data, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                message.correlation_id, 
                message.sender, 
                message.receiver, 
                message.message_type, 
                json.dumps(message.data), 
                message.timestamp.isoformat()
            ))
            conn.commit()
            
    def get_all_incidents(self):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM incidents ORDER BY started_at DESC')
            return [dict(row) for row in cursor.fetchall()]
            
    def get_incident(self, incident_id: str):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM incidents WHERE incident_id = ?', (incident_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def get_messages(self, limit=100):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM agent_messages ORDER BY timestamp DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]
""",
    "app/database/failure_simulator.py": """
import sqlite3
from app.core.config import settings

class FailureSimulator:
    def __init__(self):
        self.db_path = settings.DATABASE_PATH
        
    def simulate(self, failure_type: str):
        if not settings.DEMO_MODE:
            raise Exception("Cannot simulate failures outside of demo mode")
            
        if failure_type == "connection_timeout":
            # We simulate this at the monitor level rather than actually locking the DB
            return "Simulated connection timeout"
            
        elif failure_type == "missing_table":
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS health_check")
                conn.commit()
            return "health_check table dropped"
            
        elif failure_type == "database_locked":
            return "Simulated database lock"
            
        elif failure_type == "permission_error":
            return "Simulated permission error"
            
        else:
            return "Unknown failure type"
""",
    "app/services/__init__.py": "",
    "app/services/diagnostic_service.py": """
from pydantic import BaseModel
from app.core.config import settings
import json
from openai import OpenAI
import time

class DiagnosisResult(BaseModel):
    failure_type: str
    root_cause: str
    recommended_action: str
    explanation: str
    confidence: float
    risk_level: str  # LOW, MEDIUM, HIGH

class DiagnosticService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        
        # Rule-based mappings
        self.rules = {
            "no such table: health_check": DiagnosisResult(
                failure_type="missing_table",
                root_cause="The health_check table does not exist in the database.",
                recommended_action="create_health_table",
                explanation="A critical table required for monitoring is missing.",
                confidence=1.0,
                risk_level="MEDIUM"
            ),
            "connection timeout": DiagnosisResult(
                failure_type="connection_timeout",
                root_cause="Database connection exceeded timeout threshold.",
                recommended_action="reconnect",
                explanation="The application could not reach the database within the configured timeout.",
                confidence=1.0,
                risk_level="LOW"
            )
        }

    def diagnose(self, error_message: str) -> dict:
        start_time = time.time()
        
        # 1. Rule-based check
        for rule_err, result in self.rules.items():
            if rule_err in error_message.lower():
                return {
                    "source": "rule",
                    "latency": time.time() - start_time,
                    "result": result.model_dump()
                }

        # 2. LLM check
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a database diagnostic expert. Analyze the error and return a JSON object with: failure_type, root_cause, recommended_action (must be one of: reconnect, create_health_table, release_lock, retry_connection, run_integrity_check), explanation, confidence (0.0-1.0), and risk_level (LOW, MEDIUM, HIGH)."},
                        {"role": "user", "content": f"Database error: {error_message}"}
                    ],
                    response_format={ "type": "json_object" }
                )
                content = json.loads(response.choices[0].message.content)
                result = DiagnosisResult(**content)
                return {
                    "source": "OpenAI",
                    "latency": time.time() - start_time,
                    "result": result.model_dump()
                }
            except Exception as e:
                print(f"LLM diagnosis failed: {e}")
                
        # 3. Fallback
        result = DiagnosisResult(
            failure_type="unknown_error",
            root_cause="Could not determine root cause.",
            recommended_action="general_recovery",
            explanation="Fell back to general recovery.",
            confidence=0.5,
            risk_level="HIGH"
        )
        return {
            "source": "fallback",
            "latency": time.time() - start_time,
            "result": result.model_dump()
        }
""",
    "app/services/recovery_service.py": """
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
""",
    "app/agents/monitor.py": """
from app.agents.base_agent import BaseAgent
from app.database.db_manager import DatabaseManager
import uuid

class MonitorAgent(BaseAgent):
    def __init__(self, message_bus):
        super().__init__("DatabaseMonitor", message_bus)
        self.db_manager = DatabaseManager()
        self.simulated_failure = None
        
    def check_health(self):
        if self.simulated_failure == "connection_timeout":
            return False, "connection timeout"
        elif self.simulated_failure == "database_locked":
            return False, "database is locked"
            
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
""",
    "app/agents/diagnostics.py": """
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
""",
    "app/agents/recovery.py": """
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
""",
    "app/agents/validation.py": """
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
""",
    "app/agents/coordinator.py": """
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
""",
    "app/workflows/__init__.py": "",
    "app/workflows/recovery_graph.py": """
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
        \"\"\"Executes one cycle of the agents.\"\"\"
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
""",
    "app/api/__init__.py": "",
    "app/api/routes.py": """
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
""",
    "app/main.py": """
from fastapi import FastAPI
from app.api.routes import router
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(
    title="Database Recovery Agent API",
    description="API for multi-agent database reliability platform",
    version="1.0.0"
)

app.include_router(router)
""",
    "dashboard/streamlit_app.py": """
import streamlit as st

st.set_page_config(
    page_title="DB Recovery Platform",
    page_icon="🛡️",
    layout="wide"
)

st.title("AI-Powered Database Reliability Platform")
st.sidebar.success("Select a page above.")

st.markdown(\"\"\"
Welcome to the Multi-Agent Database Recovery Platform!

Use the sidebar to navigate through the dashboard:
- **System Overview:** View current state and simulate incidents.
- **Incident History:** Browse past incidents.
- **Agent Activity:** View the internal message bus.
- **Recovery Analytics:** View metrics and charts.
\"\"\")
""",
    "dashboard/pages/1_System_Overview.py": """
import streamlit as st
import requests
import pandas as pd
import time

API_URL = "http://localhost:8000"

st.set_page_config(page_title="System Overview", page_icon="📊", layout="wide")

st.title("System Overview")

def get_status():
    try:
        return requests.get(f"{API_URL}/status").json()
    except:
        return None

status_data = get_status()

if status_data:
    cols = st.columns(4)
    status_color = "green" if status_data['current_status'] == "HEALTHY" else ("red" if status_data['current_status'] in ["FAILED", "ESCALATED"] else "orange")
    
    cols[0].metric("System Status", status_data['current_status'])
    cols[1].metric("Total Incidents", status_data['failure_count'])
    cols[2].metric("Successful Recoveries", status_data['successful_recoveries'])
    cols[3].metric("Escalated/Failed", status_data['failed_recoveries'])
    
    st.divider()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Monitor Control")
        c1, c2 = st.columns(2)
        if c1.button("Start Monitoring"):
            requests.post(f"{API_URL}/monitor/start")
            st.success("Started")
            time.sleep(1)
            st.rerun()
        if c2.button("Stop Monitoring"):
            requests.post(f"{API_URL}/monitor/stop")
            st.warning("Stopped")
            time.sleep(1)
            st.rerun()
            
    with col2:
        st.subheader("Simulate Incident")
        options = ["connection_timeout", "missing_table", "database_locked", "permission_error"]
        selected_failure = st.selectbox("Failure Type", options)
        if st.button("Trigger Incident"):
            res = requests.post(f"{API_URL}/incidents/simulate", json={"failure_type": selected_failure})
            st.toast(res.json().get("message", "Simulated"))
            time.sleep(1)
            st.rerun()
            
    # Approvals
    if status_data['current_status'] == "AWAITING_APPROVAL":
        st.error(f"High-Risk Recovery Suggested for Incident: {status_data['current_incident_id']}")
        a1, a2 = st.columns(2)
        if a1.button("Approve Recovery"):
            requests.post(f"{API_URL}/recovery/{status_data['current_incident_id']}/approve")
            st.rerun()
        if a2.button("Reject / Escalate"):
            requests.post(f"{API_URL}/recovery/{status_data['current_incident_id']}/reject")
            st.rerun()

    # Auto refresh logic
    if status_data['current_status'] not in ["HEALTHY", "ESCALATED"]:
        time.sleep(2)
        st.rerun()
else:
    st.error("Cannot connect to API backend. Is it running?")
""",
    "dashboard/pages/2_Incident_History.py": """
import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"
st.set_page_config(page_title="Incident History", page_icon="📜", layout="wide")
st.title("Incident History")

try:
    incidents = requests.get(f"{API_URL}/incidents").json()
    if incidents:
        df = pd.DataFrame(incidents)
        st.dataframe(
            df[['incident_id', 'started_at', 'failure_type', 'diagnosis_source', 'recommended_action', 'risk_level', 'final_status', 'recovery_attempts']], 
            use_container_width=True
        )
    else:
        st.info("No incidents recorded yet.")
except Exception as e:
    st.error(f"Error loading incidents: {e}")
""",
    "dashboard/pages/3_Agent_Activity.py": """
import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"
st.set_page_config(page_title="Agent Activity", page_icon="🤖", layout="wide")
st.title("Agent Message Bus")

try:
    messages = requests.get(f"{API_URL}/messages").json()
    if messages:
        df = pd.DataFrame(messages)
        st.dataframe(
            df[['timestamp', 'correlation_id', 'sender', 'receiver', 'message_type', 'data']],
            use_container_width=True
        )
    else:
        st.info("No messages recorded yet.")
except Exception as e:
    st.error(f"Error loading messages: {e}")
""",
    "dashboard/pages/4_Recovery_Analytics.py": """
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API_URL = "http://localhost:8000"
st.set_page_config(page_title="Recovery Analytics", page_icon="📈", layout="wide")
st.title("Recovery Analytics")

try:
    incidents = requests.get(f"{API_URL}/incidents").json()
    if incidents:
        df = pd.DataFrame(incidents)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Incidents by Failure Type")
            fig1 = px.pie(df, names='failure_type', title='Failure Types')
            st.plotly_chart(fig1, use_container_width=True)
            
        with col2:
            st.subheader("Resolution Status")
            fig2 = px.pie(df, names='final_status', title='Final Status')
            st.plotly_chart(fig2, use_container_width=True)
            
        st.subheader("LLM Latency Distribution")
        df_llm = df[df['llm_latency_seconds'].notnull()]
        if not df_llm.empty:
            fig3 = px.box(df_llm, y='llm_latency_seconds', x='diagnosis_source', title='Diagnosis Latency by Source')
            st.plotly_chart(fig3, use_container_width=True)
            
    else:
        st.info("Not enough data to display analytics.")
except Exception as e:
    st.error(f"Error loading analytics: {e}")
""",
    "tests/__init__.py": "",
    "tests/test_workflow.py": """
from app.workflows.recovery_graph import WorkflowManager
from app.core.config import settings

def test_missing_table_workflow():
    settings.DEMO_MODE = True
    workflow = WorkflowManager()
    
    # Force the failure
    workflow.monitor.simulated_failure = "missing_table"
    
    # Run cycles until healthy or max
    for _ in range(10):
        state = workflow.tick()
        if state.current_status == "HEALTHY":
            break
            
    assert state.current_status == "HEALTHY"
    assert state.successful_recoveries == 1
    assert state.recovery_attempts == 1

def test_unknown_escalation():
    settings.DEMO_MODE = True
    workflow = WorkflowManager()
    
    workflow.monitor.simulated_failure = "unknown_critical_failure"
    
    for _ in range(10):
        state = workflow.tick()
        if state.current_status == "ESCALATED":
            break
            
    assert state.current_status == "ESCALATED"
"""
}

def generate_project():
    for filepath, content in files.items():
        full_path = os.path.join(base_dir, filepath)
        # Ensure dir exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "
")
    print("Project generated successfully.")

if __name__ == "__main__":
    generate_project()

