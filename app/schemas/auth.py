import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator, model_validator

# Clash Royale tags only ever use these characters (no O, so a typed O is really a 0).
CR_TAG_CHARS = "0289PYLQGRJCUV"
CR_TAG_RE = re.compile(rf"^#[{CR_TAG_CHARS}]{{3,12}}$")
FRIEND_LINK_RE = re.compile(
    r"(?:https?://)?link\.clashroyale\.com/\?supercell_id&p=(\d+-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}"
    r"-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})",
    re.IGNORECASE,
)
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
PHONE_RE = re.compile(r"^\+\d{8,15}$")


def normalize_cr_tag(value: str) -> str:
    tag = value.strip().upper().replace("O", "0")
    if not tag.startswith("#"):
        tag = "#" + tag
    return tag


def normalize_phone(value: str) -> str:
    phone = re.sub(r"[\s\-().]", "", value)
    if re.fullmatch(r"\d{10}", phone):
        phone = "+1" + phone
    return phone


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    cr_player_tag: str
    phone_number: str | None = None
    sms_consent: bool = False
    supercell_id_link: str

    @field_validator("username")
    @classmethod
    def check_username(cls, v: str) -> str:
        v = v.strip()
        if not USERNAME_RE.fullmatch(v):
            raise ValueError("Username must be 3-20 letters, digits, or underscores")
        return v

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("cr_player_tag")
    @classmethod
    def check_cr_player_tag(cls, v: str) -> str:
        tag = normalize_cr_tag(v)
        if not CR_TAG_RE.fullmatch(tag):
            raise ValueError(
                f"Player tag must be # followed by 3-12 of these characters: {CR_TAG_CHARS}"
            )
        return tag

    @field_validator("supercell_id_link")
    @classmethod
    def check_supercell_id_link(cls, v: str) -> str:
        match = FRIEND_LINK_RE.search(v)
        if match is None:
            raise ValueError(
                "Friend link must look like https://link.clashroyale.com/?supercell_id&p=..."
            )
        return f"https://link.clashroyale.com/?supercell_id&p={match.group(1).lower()}"

    @field_validator("phone_number")
    @classmethod
    def check_phone_number(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return None
        phone = normalize_phone(v)
        if not PHONE_RE.fullmatch(phone):
            raise ValueError("Phone number must be in international format, e.g. +15551234567")
        return phone

    @model_validator(mode="after")
    def require_phone_for_sms(self) -> "UserCreate":
        if self.sms_consent and self.phone_number is None:
            raise ValueError("A phone number is required to receive SMS match invites")
        return self


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    cr_player_tag: str
    phone_number: str | None = None
    sms_consent: bool
    supercell_id_link: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
