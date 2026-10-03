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
