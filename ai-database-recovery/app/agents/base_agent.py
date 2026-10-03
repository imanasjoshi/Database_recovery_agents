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
