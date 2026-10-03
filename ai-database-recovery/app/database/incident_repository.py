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
