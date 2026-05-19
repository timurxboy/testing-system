from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.db.engine import engine
from core.db.factory.session import create_session_maker

SessionLocal: async_sessionmaker[AsyncSession] = create_session_maker(engine)
