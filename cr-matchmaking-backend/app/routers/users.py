from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import (
    LinkCRAccountRequest,
    LinkCRAccountResponse,
    UserResponse,
    UserStatsResponse,
    UserUpdate,
    VerifyCRAccountRequest,
    VerifyCRAccountResponse,
)
from app.services import user_service
from app.utils.redis_client import get_redis

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    update: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    updated = await user_service.update_user(db, user, update)
    return UserResponse.model_validate(updated)


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_my_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserStatsResponse:
    return await user_service.get_stats(db, user.user_id)


@router.post("/me/link-cr", response_model=LinkCRAccountResponse)
async def link_cr(
    request: LinkCRAccountRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> LinkCRAccountResponse:
    return await user_service.link_cr_account(db, redis, user, request)


@router.post("/me/verify-cr", response_model=VerifyCRAccountResponse)
async def verify_cr(
    request: VerifyCRAccountRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> VerifyCRAccountResponse:
    return await user_service.verify_cr_account(db, redis, user, request)
