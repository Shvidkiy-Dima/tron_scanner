import asyncio
import logging
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional

from aiohttp import ContentTypeError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from tronpy.keys import to_base58check_address

from models import Transaction, Wallet, Currency, WalletBalance, Token, Block

from settings import Config
from utils.common import format_date
from utils.common import parse_txs, TransactionSchema
from utils.tron import TronAPI
from utils.tron import get_balance, get_trc20_balance
from db import init_db

logger = logging.getLogger(__name__)


class TronScanner(ABC):

    def __init__(self):
        self.blockchain = 'TRON'


    def run(self):
        print(1)
        asyncio.run(self._start())

    async def _start(self):
        async with init_db() as engine:
            await self._start_listening(engine)

    async def _start_listening(self, engine):
        print(1)
        next_block_num = (await self._get_next_block_num(engine))
        print(next_block_num)
        while True:
            try:
                async with TronAPI(Config.API_KEY) as tapi:
                    # Получаем сразу несколько блоков чтоб меньше долбить апи
                    blocks = (await tapi.get_blocks_by_num_range(next_block_num)) or list()
                    last_block_num = None

                    async with AsyncSession(bind=engine) as session:
                        for block in blocks:
                            # обходим блок
                            await self._process_block(block, engine)
                            last_block_num = block['block_header']['raw_data']['number']
                            session.add(Block(num=last_block_num, blockchain=self.blockchain))
                            await session.commit()

                    if last_block_num is not None:
                        next_block_num = last_block_num + 1

            except ContentTypeError:
                pass
            except Exception as e:
                # Если произошла ошибка то начинаем обрабатывать с последнего блока занаво
                logger.exception(f'\n\nError process block - {next_block_num} \n\n {e}')

    async def _get_next_block_num(self, engine):
        """
        Return last_block_num+1 from BD or last_block_num from API
        """
        async with AsyncSession(bind=engine) as session:
            last_block = (await session.execute(select(Block).order_by(-Block.num))).scalars().first()
            last_block_num = last_block.num + 1 if last_block else None

        if last_block_num is None:
            async with TronAPI(Config.API_KEY) as tapi:
                print(444)
                last_block_num = await tapi.get_last_block_num()
                print(last_block_num)

        return last_block_num

    async def _process_block(self, next_block: dict, engine):
        block_num = next_block['block_header']['raw_data']['number']
        txs = next_block.get('transactions')

        if txs is None and next_block.get('blockID'):
            logger.info(f'CUR block {block_num}: no txs in block')
            # Block doesnt have txs
            return

        logger.info(f'Current block {block_num} {Config.TRON_NODE}')

        # TODO: вынести обновление кошельков в отдельный Task, чтобы не перегружать БД
        async with AsyncSession(bind=engine, expire_on_commit=False) as session:
            wallets = set((await session.execute(select(Wallet.address))).scalars().all())
            contracts = (await session.execute(
                         select(Token).options(selectinload(Token.currency))
                          )).scalars().all()
            contracts = {token.contract_address: {'name': token.name, 'dec': token.decimals} for token in contracts}

        txs = parse_txs(txs, wallets, contracts)
        for tx in txs:
            try:
                await self._process_tx(tx, block_num, engine)
            except Exception as e:
                logger.exception(f'Transaction error {tx.tx_id}: {e}')
    async def _process_tx(self, tx: TransactionSchema, block_num: int, engine):

        async with AsyncSession(bind=engine, expire_on_commit=False) as session:

            if await (await session.execute(select(Transaction).where(Transaction.txid == tx.tx_id))).scalar() is not None:
                logger.info(f'Транзакция {tx.tx_id} уже есть в базе')
                return

            wallet = (await session.execute(select(Wallet).where(Wallet.address == tx.to_address)
                                       .options(selectinload(Wallet.user)))).scalar()

            if wallet is None:
                logger.info(f'адреса {tx.to_address} нет в базе')
                return

            currency = (await session.execute(select(Currency).where(Currency.name == tx.currency_name))).scalar()
            logger.info(
                f'Новая входящая транзакция: {tx.from_address} -> {tx.to_address} {tx.amount} {tx.currency_name} {tx.tx_id}')

            new_tx = Transaction(
                block_num=str(block_num),
                txid=tx.tx_id,
                from_address=tx.from_address,
                to_address=tx.to_address,
                blockchain='TRX',
                amount=tx.amount,
                currency=currency,
                time=format_date(tx.time),
                purpose=Transaction.TransactionType.DEPOSIT,
                status=Transaction.TransactionStatus.SUCCESS,
                trc20=tx.trc20
            )

            session.add(new_tx)
            await session.commit()


TronScanner().run()
