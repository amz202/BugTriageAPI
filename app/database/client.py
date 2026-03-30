import asyncpg

class DatabaseState:
    """Holds the asynchronous database connection pool."""
    pool: asyncpg.Pool = None

db_state = DatabaseState()