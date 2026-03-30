import os
from pydantic import BaseModel

class Settings(BaseModel):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://bug_user:admin@127.0.0.1:5432/bugtriage"
    )

settings = Settings()