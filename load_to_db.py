import os
import asyncio
import csv
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import init_db
from models import Wallet, Currency, Token, Block
from settings.base import BaseConfig


currencies = [('TRX', 6), ('USDT', 6)]

async def _load_to_db(wallets):
    async with init_db() as engine:
        session = AsyncSession(bind=engine)

        c = (await session.execute(select(Currency).where(Currency.name == 'USDT'))).scalar()
        if not c:
            c = Currency(name='USDT', decimals=6)

        t = (await session.execute(select(Token).where(
            Token.contract_address==BaseConfig.USDT_CONTRACT, Token.currency==c))).scalar()
        if not t:
            t = Token(decimals=6, contract_address=BaseConfig.USDT_CONTRACT, currency=c)

        session.add(t)
        session.add(c)
        for a in wallets:
            if (await session.execute(select(Wallet).where(Wallet.address == a))).scalar():
                continue

            session.add(Wallet(address=a))

        for name, d in currencies:
            if not (await session.execute(select(Currency).where(Currency.name == name))).scalar():
                session.add(Currency(name=name, decimals=d))

        await session.commit()
        await session.close()


if __name__ == '__main__':
    import csv

    wallets = [ ]
    with open('tron_wallets.csv', newline='') as csvfile:

        spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')

        for row in spamreader:
            wallets.append(row[0])

    asyncio.run(_load_to_db(wallets))
