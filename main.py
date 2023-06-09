import asyncio
from fastapi import FastAPI
import uvicorn
from settings import Config
from database import engine
from scanner import TronScanner
from sqlalchemy.ext.asyncio import AsyncSession
from models import Transaction
from sqlalchemy import select, func

def get_app() -> FastAPI:
    fast_api = FastAPI()

    return fast_api


app = get_app()


scanner = TronScanner()


@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()


@app.get('/txs')
async def get_txs():
    async with AsyncSession(bind=engine) as session:
        txs = (await session.execute(select(Transaction))).scalars().all()


    res = [
        {
            'contract_address': t.contract_address,
            'block_num': t.block_num,
            'txid': t.txid,
            'from_address': t.from_address,
            'to_address': t.to_address,
            'time': t.time,
            'currency_name': t.currency_name

        }

        for t in txs
    ]

    return res


@app.get('/txs/{wallet}')
async def get_txs_by_wallet(wallet: str):
    async with AsyncSession(bind=engine) as session:
        txs = (await session.execute(select(Transaction).where(func.lower(Transaction.to_address)==wallet.lower()))).scalars().all()

    res = [
        {
            'contract_address': t.contract_address,
            'block_num': t.block_num,
            'txid': t.txid,
            'from_address': t.from_address,
            'to_address': t.to_address,
            'time': t.time,
            'currency_name': t.currency_name

        }

        for t in txs
    ]

    return res

@app.on_event("startup")
async def shutdown():
    TronScanner.TASK = asyncio.create_task(scanner._start())



if __name__ == '__main__':
    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
    )