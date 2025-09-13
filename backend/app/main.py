from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine
from .auth import router as auth_router, get_current_user
from .rooms import router as ws_router

app = FastAPI(title="Just Chat A Moment API")

# CORS（前端开发友好）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(auth_router, prefix="/api")
app.include_router(ws_router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/me")
async def read_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "avatar_url": current_user.avatar_url,
    }