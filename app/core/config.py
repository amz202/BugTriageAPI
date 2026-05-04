from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    AUTO_ASSIGN_THRESHOLD: float = 0.75

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Module-level convenience constant for direct imports
AUTO_ASSIGN_THRESHOLD = settings.AUTO_ASSIGN_THRESHOLD
