from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.user import User
from lastro.schemas.auth import LoginRequest, LoginResponse
from lastro.services.auth.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest, session: AsyncSession = Depends(get_session)
) -> LoginResponse:
    result = await session.exec(select(User).where(User.username == payload.username))
    user = result.first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="usuário ou senha inválidos")
    return LoginResponse(access_token=create_access_token(user.username))
