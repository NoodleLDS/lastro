from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.core.config import settings
from lastro.models.user import User
from lastro.services.auth.security import hash_password


async def ensure_admin_user(session: AsyncSession) -> None:
    result = await session.exec(select(User).where(User.username == settings.admin_username))
    if result.first() is not None:
        return
    session.add(
        User(
            username=settings.admin_username,
            password_hash=hash_password(settings.admin_password),
        )
    )
    await session.commit()
