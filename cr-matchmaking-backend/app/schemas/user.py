import uuid

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    username: str
    cr_player_tag: str | None = None
    cr_player_verified: bool = False
    trophy_level: int | None = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None


class LinkCRAccountRequest(BaseModel):
    player_tag: str = Field(pattern=r"^#[A-Z0-9]+$")


class VerifyCRAccountRequest(BaseModel):
    verification_code: str = Field(min_length=5, max_length=5)


class VerifyCRAccountResponse(BaseModel):
    verified: bool
    player_tag: str
    player_name: str
    trophy_level: int


class UserStatsResponse(BaseModel):
    total_matches: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    win_rate: float = 0.0
    lifetime_wagered: float = 0.0
    lifetime_won: float = 0.0
