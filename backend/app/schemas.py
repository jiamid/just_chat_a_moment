from pydantic import BaseModel, EmailStr, Field


class SesSign(BaseModel):
    email: EmailStr
    expires_at: int
    sign: str


class UserCreate(SesSign):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=64)
    avatar_url: str | None = None


class UserRead(BaseModel):
    id: int
    email: EmailStr
    username: str
    avatar_url: str | None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
