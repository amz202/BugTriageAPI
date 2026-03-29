from supabase import create_client, Client
from app.core.config import settings

# Validate configuration before initializing connection
settings.validate_supabase_config()

# Instantiate the Supabase client
supabase_client: Client = create_client(
    supabase_url=settings.SUPABASE_URL,
    supabase_key=settings.SUPABASE_KEY
)