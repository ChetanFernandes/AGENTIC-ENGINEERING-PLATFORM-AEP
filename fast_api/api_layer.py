from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

from logger.log import setup_logging
log = setup_logging()

from fast_api.service_layer import ServiceLayer
from app.schemas.fast_api_schema import PayloadData


service_layer = ServiceLayer()

@asynccontextmanager
async def lifespan(app:FastAPI):
    loop = asyncio.get_running_loop()

    await service_layer.initialize_mcp_checkpointer()
    log.info("Application started")
    yield
    log.info("Shutting down AEP application")


app = FastAPI(title = "AEP", lifespan = lifespan)

@app.get("/")
def app_testing():
    return "Welcome to Agentic AEP Platforms"

@app.post('/chat')
async def user_input(data:PayloadData):
    try:
        result = await service_layer.get_payload_data(data.user_name, data.thread_id , data.question)
        return result
    except Exception:
        log.exception("Error while receving the payload from UI")
        raise




