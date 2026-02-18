import random
import string
import uuid

from redis.asyncio import Redis
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match import MATCH_STATUS_COMPLETED, Match
from app.models.user import User, UserBalance
from app.schemas.user import (
    LinkCRAccountRequest,
    LinkCRAccountResponse,
    UserStatsResponse,
    UserUpdate,
    VerifyCRAccountRequest,
    VerifyCRAccountResponse,
)
from app.services import cr_api_service
from app.utils.exceptions import AppException


async def update_user(db: AsyncSession, user: User, update: UserUpdate) -> User:
    if update.username is not None:
        result = await db.execute(
            select(User).where(
                User.username == update.username, User.user_id != user.user_id
            )
        )
        if result.scalar_one_or_none():
            raise AppException(
                code="USERNAME_TAKEN",
                message="Username already taken",
                status_code=409,
            )
        user.username = update.username

    if update.email is not None:
        result = await db.execute(
            select(User).where(
                User.email == update.email, User.user_id != user.user_id
            )
        )
        if result.scalar_one_or_none():
            raise AppException(
                code="EMAIL_TAKEN",
                message="Email already registered",
                status_code=409,
            )
        user.email = update.email

    await db.commit()
    await db.refresh(user)
    return user


async def get_stats(db: AsyncSession, user_id: uuid.UUID) -> UserStatsResponse:
    total_result = await db.execute(
        select(func.count(Match.match_id)).where(
            or_(Match.player1_id == user_id, Match.player2_id == user_id),
            Match.status == MATCH_STATUS_COMPLETED,
        )
    )
    total = total_result.scalar() or 0

    wins_result = await db.execute(
        select(func.count(Match.match_id)).where(
            Match.winner_id == user_id,
            Match.status == MATCH_STATUS_COMPLETED,
        )
    )
    wins = wins_result.scalar() or 0

    losses = total - wins
    win_rate = (wins / total * 100) if total > 0 else 0.0

    balance_result = await db.execute(
        select(UserBalance).where(UserBalance.user_id == user_id)
    )
    balance = balance_result.scalar_one_or_none()

    return UserStatsResponse(
        total_matches=total,
        wins=wins,
        losses=losses,
        win_rate=round(win_rate, 1),
        lifetime_wagered=float(balance.lifetime_wagered) if balance else 0.0,
        lifetime_won=float(balance.lifetime_won) if balance else 0.0,
    )


def _generate_verification_code() -> str:
    return "".join(random.choices(string.digits, k=5))


async def link_cr_account(
    db: AsyncSession, redis: Redis, user: User, request: LinkCRAccountRequest
) -> LinkCRAccountResponse:
    player_data = await cr_api_service.get_player(request.player_tag)

    result = await db.execute(
        select(User).where(
            User.cr_player_tag == request.player_tag,
            User.user_id != user.user_id,
        )
    )
    if result.scalar_one_or_none():
        raise AppException(
            code="TAG_ALREADY_LINKED",
            message="This player tag is linked to another account",
            status_code=409,
        )

    code = _generate_verification_code()
    await redis.setex(
        f"cr_verify:{user.user_id}",
        600,  # 10 minutes
        f"{request.player_tag}:{code}",
    )

    user.cr_player_tag = request.player_tag
    user.cr_player_verified = False
    await db.commit()

    return LinkCRAccountResponse(
        player_tag=request.player_tag,
        player_name=player_data.get("name", ""),
        verification_code=code,
        instructions=f"Set your Clash Royale in-game name to include '{code}', then call verify.",
    )


async def verify_cr_account(
    db: AsyncSession, redis: Redis, user: User, request: VerifyCRAccountRequest
) -> VerifyCRAccountResponse:
    stored = await redis.get(f"cr_verify:{user.user_id}")
    if not stored:
        raise AppException(
            code="NO_PENDING_VERIFICATION",
            message="No pending verification. Link your CR account first.",
            status_code=400,
        )

    player_tag, expected_code = stored.rsplit(":", 1)

    if request.verification_code != expected_code:
        raise AppException(
            code="INVALID_CODE",
            message="Verification code does not match",
            status_code=400,
        )

    player_data = await cr_api_service.get_player(player_tag)
    player_name = player_data.get("name", "")

    if expected_code not in player_name:
        raise AppException(
            code="CODE_NOT_IN_NAME",
            message="Verification code not found in your in-game name",
            status_code=400,
        )

    trophies = player_data.get("trophies", 0)
    user.cr_player_tag = player_tag
    user.cr_player_verified = True
    user.trophy_level = trophies
    await db.commit()
    await db.refresh(user)

    await redis.delete(f"cr_verify:{user.user_id}")

    return VerifyCRAccountResponse(
        verified=True,
        player_tag=player_tag,
        player_name=player_name,
        trophy_level=trophies,
    )
