from sqlalchemy.ext.asyncio import create_async_engine
from contextlib import asynccontextmanager
import models


@asynccontextmanager
async def init_db():
    from settings import Config
    db_name = Config.DB_NAME
    db_user = Config.DB_USER
    db_password = Config.DB_PASSWORD
    db_host = Config.DB_HOST

    if not all([db_host, db_user, db_name]):
        raise RuntimeError('You have to set DB_NAME DB_USER DB_PASSWORD DB_HOST in config')

    engine = create_async_engine(f'postgresql+asyncpg://{db_user}:{db_password}@{db_host}/{db_name}')

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()
