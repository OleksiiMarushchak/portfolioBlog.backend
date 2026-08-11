from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str


    referral_only: bool

    ACCESS_TOKEN_EXPIRE_MINUTES:int
    REFRESH_TOKEN_EXPIRE_DAYS:int
    ALGORITHM:str
    SECRET_KEY:str



    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()