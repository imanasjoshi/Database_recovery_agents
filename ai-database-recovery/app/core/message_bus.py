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
