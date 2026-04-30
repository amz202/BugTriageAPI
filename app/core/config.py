from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Existing settings
    DATABASE_URL: str

    # Phase 1 Security Additions
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Pydantic V2 Config syntax
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()