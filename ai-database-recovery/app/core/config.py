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
