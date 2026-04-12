from uvicorn import run


if __name__ == "__main__":
    run(
        app="routers.api_v1_router:app",
        reload=True,
        log_level="debug",
        host="localhost",
        port=8000,
    )
