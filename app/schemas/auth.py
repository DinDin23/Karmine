from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    cr_player_tag: str
    phone_number: str
    supercell_id_link: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    cr_player_tag: str
    phone_number: str
    supercell_id_link: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
