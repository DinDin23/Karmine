import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User, UserBalance
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.schemas.user import UserResponse
from app.utils.exceptions import AppException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise AppException(
                code="INVALID_TOKEN", message="Invalid token", status_code=401
            )
        return uuid.UUID(user_id)
    except JWTError:
        raise AppException(
            code="INVALID_TOKEN",
            message="Invalid or expired token",
            status_code=401,
        )


async def register(db: AsyncSession, request: RegisterRequest) -> AuthResponse:
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise AppException(
            code="EMAIL_TAKEN",
            message="Email already registered",
            status_code=409,
        )

    result = await db.execute(select(User).where(User.username == request.username))
    if result.scalar_one_or_none():
        raise AppException(
            code="USERNAME_TAKEN",
            message="Username already taken",
            status_code=409,
        )

    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        username=request.username,
    )
    db.add(user)
    await db.flush()  # populate user_id before creating balance

    balance = UserBalance(user_id=user.user_id)
    db.add(balance)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.user_id)
    return AuthResponse(token=token, user=UserResponse.model_validate(user))


async def login(db: AsyncSession, request: LoginRequest) -> AuthResponse:
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise AppException(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password",
            status_code=401,
        )

    token = create_access_token(user.user_id)
    return AuthResponse(token=token, user=UserResponse.model_validate(user))
