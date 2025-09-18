from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import  OAuth2PasswordRequestForm
from fastapi.background import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from db.db import get_db
from models.models import User
from schemas.schemas import UserCreate, UserRead, Token, SesSign, EmailBase, SesSignResponse, UserReadResponse, TokenResponse
from service.sms_service import email_bot
from config.auth import get_password_hash,verify_password,create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/gen_sms", response_model=SesSignResponse)
async def gen_sms(user: EmailBase, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    # 检查邮箱、用户名唯一
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    code, expires_at, sign = email_bot.generate_code(300, user.email)
    logger.info(f"code={code}, expires_at={expires_at}, sign={sign}")
    ses_sign = SesSign(
        email=user.email,
        expires_at=expires_at,
        sign=sign
    )
    background_tasks.add_task(email_bot.async_send_email, email=user.email,code=code)
    return SesSignResponse(data=ses_sign)


@router.post("/register", response_model=UserReadResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # 检查邮箱、用户名唯一
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="Username already taken")

    # 校验邮箱验证码
    is_valid, message = email_bot.verify_code(user_in.code, user_in.expires_at, user_in.sign, user_in.email)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    user = User(
        email=user_in.email,
        username=user_in.username,
        avatar_url=user_in.avatar_url,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserReadResponse(data=user)


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token({"sub": str(user.id)})
    return TokenResponse(data=Token(access_token=access_token))

