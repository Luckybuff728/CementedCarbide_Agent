from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..security import hash_password, verify_password, create_access_token
from ...models.user import User


class UserCreate(BaseModel):
    username: str
    password: str
    display_name: str | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str | None
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    user = User(
        username=user_in.username,
        password_hash=hash_password(user_in.password),
        display_name=user_in.display_name,
        role="user",
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_in.username).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或密码错误")
    token = create_access_token(str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/wechat/qrcode")
def wechat_qrcode():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="微信扫码登录暂未实现")


@router.get("/wechat/status")
def wechat_status():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="微信扫码登录暂未实现")
