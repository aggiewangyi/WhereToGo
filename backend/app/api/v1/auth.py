"""ToC 用户：注册、登录、当前用户。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.core.security import create_access_token, verify_password
from app.crud.user import crud_user
from app.models.user import User
from app.schemas.user import TokenOut, UserLogin, UserOut, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
async def register(body: UserRegister, db: AsyncSession = Depends(get_session)):
    existing = await crud_user.get_by_phone(db, body.phone)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该手机号已注册")
    user = await crud_user.create(db, obj_in=body)
    await db.commit()
    await db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return TokenOut(access_token=token)


@router.post("/login", response_model=TokenOut)
async def login(body: UserLogin, db: AsyncSession = Depends(get_session)):
    user = await crud_user.get_by_phone(db, body.phone)
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号不可用")
    token = create_access_token({"sub": str(user.id)})
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
async def read_me(current: User = Depends(get_current_user)):
    return current
