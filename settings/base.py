import os


class BaseConfig:
    DB_NAME = os.environ.get('POSTGRES_DB', 'wallet')
    DB_USER = os.environ.get('POSTGRES_USER', 'admin')
    DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'admin')
    DB_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
    DB_PORT = os.environ.get('POSTGRES_PORT', 5432)
    DB_URL = f'postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'

    USDT_CONTRACT = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'
    API_KEY = os.environ.get('API_KEY', '04d8419d-953a-48cd-a2fb-48b2830fbc96')
    NETWORK = 'mainnet'
    TRON_HOST = 'api.trongrid.io'
    TRON_NODE = f'https://{TRON_HOST}/'

    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = os.environ.get('PORT', 8000)

    @classmethod
    def get(cls, value):
        return getattr(cls, value, None)
