from fastapi import FastAPI
from routers.api_v1_router import api_router

app = FastAPI(title="Custom Auth System")
app.include_router(api_router, prefix="/api/v1")
