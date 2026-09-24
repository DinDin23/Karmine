import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserOut
from app.services import cr_api_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    uniqueness_filters = [
        User.email == payload.email,
        User.username == payload.username,
        User.cr_player_tag == payload.cr_player_tag,
    ]
    if payload.phone_number:
        uniqueness_filters.append(User.phone_number == payload.phone_number)

    existing = db.query(User).filter(or_(*uniqueness_filters)).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username, email, CR player tag, or phone number already registered",
        )

    # A well-formed but mistyped tag would register fine and then never settle,
    # so confirm the player actually exists. Fail closed if the CR API can't answer.
    try:
        tag_exists = cr_api_service.player_exists(payload.cr_player_tag)
    except httpx.HTTPError:
        logger.exception("CR API player lookup failed for %s", payload.cr_player_tag)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Couldn't verify your Clash Royale player tag right now. Please try again shortly.",
        )
    if not tag_exists:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No Clash Royale player found with tag {payload.cr_player_tag}. Double-check it in your in-game profile.",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        cr_player_tag=payload.cr_player_tag,
        phone_number=payload.phone_number,
        sms_consent=payload.sms_consent,
        supercell_id_link=payload.supercell_id_link,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id))
    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
