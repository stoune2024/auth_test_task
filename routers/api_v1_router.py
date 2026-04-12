from fastapi import FastAPI
from uvicorn import run
from apps.user.repository import init_db
from apps.user.controllers import user_router
from apps.auth.controllers import auth_router


app = FastAPI(
    title="Custom Auth System",
    description="""
    Среди не защищенных маршрутов находятся:
    /docs - Документация Swagger
    /redoc - альтернативная документация
    """,
    openapi_prefix="/api/v1",
)

app.include_router(user_router, prefix="/user")
app.include_router(auth_router, prefix="/auth")


@app.on_event("startup")
async def startup_event():
    await init_db()
