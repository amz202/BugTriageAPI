import os
from pydantic import BaseModel

class Settings(BaseModel):
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    def validate_supabase_config(self):
        """Validates credentials."""
        if not self.SUPABASE_URL or not self.SUPABASE_KEY:
            raise ValueError("environment variables must be set.")

settings = Settings()