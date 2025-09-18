from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from db.db import Base, engine
from register import register_router
from config.settings import settings
from loguru import logger


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("🚀 Starting Application")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info(f"Docs http://127.0.0.1:8000/docs")
    yield
    logger.info("⛔ Stopping Application")


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# CORS（前端开发友好）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

register_router(app)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

