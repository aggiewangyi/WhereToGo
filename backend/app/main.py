from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_v1_router
from app.core.config import get_settings
from app.core.database import engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify DB connectivity
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: None)
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Travel planning agent as an HTTP tool service (LangGraph / multi-agent).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
