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
