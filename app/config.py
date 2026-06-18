from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    cr_api_key: str

    class Config:
        env_file = ".env"


settings = Settings()
