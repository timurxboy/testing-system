from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine


def create_engine(
    db_url: str,
    *,
    echo: bool = False,
    pool_size: int = 10,
    max_overflow: int = 20,
) -> AsyncEngine:
    return create_async_engine(
        db_url,
        echo=echo,
        pool_size=pool_size,
        max_overflow=max_overflow,
    )
