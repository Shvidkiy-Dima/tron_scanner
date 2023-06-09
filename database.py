from sqlalchemy.ext.asyncio import create_async_engine
from settings import Config


engine = create_async_engine(Config.DB_URL)