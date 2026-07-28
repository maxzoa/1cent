from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from onecent.config import get_settings

engine: AsyncEngine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
Session = async_sessionmaker(engine, expire_on_commit=False)
