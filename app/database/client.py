from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Initialize the asynchronous engine with connection pooling parameters
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True to log SQL queries during debugging
    pool_size=20,
    max_overflow=10,
    future=True
)

# Create the session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db() -> AsyncSession:
    """
    FastAPI dependency that yields an asynchronous database session.
    Ensures transactions are isolated and connections are returned to the pool.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()