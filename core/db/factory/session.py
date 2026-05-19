from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine


def create_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
