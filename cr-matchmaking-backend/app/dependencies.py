from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services import auth_service
from app.utils.exceptions import AccountNotVerified, AppException

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = auth_service.decode_access_token(credentials.credentials)

    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise AppException(
            code="USER_NOT_FOUND", message="User not found", status_code=401
        )

    return user


async def require_verified_cr_account(
    user: User = Depends(get_current_user),
) -> User:
    if not user.cr_player_verified:
        raise AccountNotVerified()
    return user
