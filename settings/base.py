import os


class BaseConfig:
    DB_NAME = os.environ.get('POSTGRES_DB', 'wallet')
    DB_USER = os.environ.get('POSTGRES_USER', 'admin')
    DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'admin')
    DB_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
    DB_PORT = os.environ.get('POSTGRES_PORT', 5432)

    USDT_CONTRACT = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'
    API_KEY = '' #'59ab76cb-26e6-47f1-81dd-67c6556c3a33'
    NETWORK = 'mainnet'
    TRON_HOST = 'api.trongrid.io'
    TRON_NODE = f'https://{TRON_HOST}/'

    @classmethod
    def get(cls, value):
        return getattr(cls, value, None)
