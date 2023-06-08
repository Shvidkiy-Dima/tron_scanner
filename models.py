from sqlalchemy import BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from decimal import Decimal
from typing import Union, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy import Column, String, DateTime, INTEGER, ForeignKey, \
    Numeric, BIGINT, Boolean, text


Base = declarative_base()




class BaseCurrency(Base):
    __abstract__ = True

    decimals = Column(INTEGER, nullable=False)
    name = Column(String(16), primary_key=True)

    def to_decimal(self, value: Union[int, str, Decimal]) -> Decimal:
        return self.round(Decimal(value).scaleb(-int(self.decimals)))

    def round(self, d: Decimal) -> Decimal:
        return Decimal(round(d, self.decimals))

    def decimal_string(self, value: Decimal) -> str:
        return f'{value:.{self.decimals}f}'.rstrip('0').rstrip('.')

    def int_value(self, value: Decimal) -> int:
        value = Decimal(value)
        return int(value.scaleb(self.decimals))

    def human_string(self, value) -> str:
        return f'{self.decimal_string(value)} {self.name}'


class BaseModel(Base):
    __abstract__ = True
    _query_property = None

    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Block(Base):
    __tablename__ = 'block'

    blockchain = Column(String(16), nullable=False)
    num = Column(BigInteger, primary_key=True)


class Currency(BaseCurrency):
    """
    Валюты
    """
    __tablename__ = 'currencies'

    name = Column(String(16), primary_key=True)
    decimals = Column(INTEGER, nullable=False)
    disabled = Column(Boolean, server_default='false', nullable=False)

    transactions = relationship(
        'Transaction',
        back_populates='currency',
    )
    tokens = relationship('Token', back_populates='currency')
    cryptocurrency = relationship(
        'Cryptocurrency',
        back_populates='currency',
        uselist=False
    )

    @staticmethod
    async def get_all(
            session: AsyncSession,
            blockchain: str = None
    ) -> List['Currency']:
        stmt = select(Currency).where(Currency.disabled == False).options(
            selectinload(Currency.tokens)
        )
        if blockchain is not None:
            stmt = stmt.join(Token, Token.name == Currency.name).where(
                Token.blockchain == blockchain)
        cur = await session.execute(stmt)
        return cur.scalars().all()

    @staticmethod
    async def get_by_name(session: AsyncSession, name: str, blockchain: str = None) -> 'Currency':
        stmt = select(Currency).where(Currency.name == name).where(
            Currency.disabled == False).join(
            Currency.tokens,
            isouter=True
        )
        if blockchain is not None:
            stmt = stmt.where(
                Token.blockchain == blockchain
            )
        cur = await session.execute(stmt)
        return cur.scalar()

    @property
    def contract_address(self):
        if self.tokens:
            for t in self.tokens:
                if t.blockchain == 'ETH':
                    return t.contract_address
        return None

    def get_contract_address(self, blockchain: str):
        if self.tokens:
            for t in self.tokens:
                if t.blockchain == blockchain:
                    return t.contract_address
        raise ValueError(f'{self.name = } {self.tokens = } {blockchain = }')

    def __repr__(self):
        return f'{self.name}'


class Token(BaseCurrency):
    """
    Токены
    """
    __tablename__ = 'tokens'

    contract_address = Column(String(64), primary_key=True)
    decimals = Column(INTEGER, nullable=False, server_default=text('18'))

    name = Column(String(16), ForeignKey(Currency.name))
    currency = relationship('Currency', back_populates='tokens')

    @staticmethod
    async def get_by_contract(session: AsyncSession,
                              contract_address: str) -> 'Token':
        token = await session.execute(
            select(Token).where(Token.contract_address == contract_address))
        return token.scalar()


class Wallet(BaseModel):
    __tablename__ = 'wallets'

    id = Column(INTEGER, primary_key=True)

    address = Column(String(64), unique=True, index=True, nullable=False) # TODO: PK ?

    balances = relationship('WalletBalance', back_populates='wallet')

    def __repr__(self):
        return f'[Wallet user:{self.user} address:{self.address}]'


    async def get_tx_in_by_txid(
            self,
            session: AsyncSession,
            txid: str
    ) -> 'Transaction':
        db_tx = await session.execute(select(Transaction).where(
            Transaction.txid == txid,
            Transaction.to_address == self.address
        ).options(
            selectinload(Transaction.currency)
        ))
        return db_tx.scalar()

    async def get_tx_out_by_txid(self, session: AsyncSession,
                                 txid: str) -> 'Transaction':
        db_tx = await session.execute(select(Transaction).where(
            Transaction.txid == txid,
            Transaction.from_address == self.address
        ).options(
            selectinload(Transaction.currency)
        ))
        return db_tx.scalar()

    async def get_balance(self, session: AsyncSession,
                          currency_name: str) -> 'WalletBalance':
        balance = await session.execute(
            select(WalletBalance).where(
                WalletBalance.wallet_id == self.id,
                WalletBalance.currency_name == currency_name
            ))
        return balance.scalar()



class WalletBalance(BaseModel):
    __tablename__ = 'wallet_balances'

    id = Column(INTEGER, primary_key=True)

    wallet_id = Column(INTEGER, ForeignKey(Wallet.id))
    wallet = relationship(Wallet, back_populates='balances')

    currency_name = Column(String(16), ForeignKey(Currency.name))
    currency = relationship('Currency')

    amount = Column(Numeric, nullable=False, default=0) # TODO: decimal



class Transaction(Base):
    __tablename__ = 'transactions'

    class TransactionType:
        DEPOSIT = 'deposit'
        WITHDRAW = 'withdraw'
        TRANSFER = 'transfer'

    class TransactionStatus:
        SUCCESS = 'success'
        PENDING = 'pending'

    id = Column(INTEGER, primary_key=True)

    contract_address = Column(String(64), ForeignKey(Token.contract_address))
    currency_name = Column(String(16), ForeignKey(Currency.name), nullable=True)
    currency = relationship('Currency', back_populates='transactions')

    block_num = Column(String(256), nullable=True)
    txid = Column(String(66), nullable=False) # TODO: uniq and PK?
    from_address = Column(String(64), nullable=True, index=True) # TODO: nullable=True ?
    to_address = Column(String(64), nullable=False, index=True)
    purpose = Column(String(16), nullable=False)
    status = Column(String(16), nullable=False, default=TransactionStatus.PENDING)
    time = Column(DateTime(timezone=True),  default=datetime.utcnow)
    trc20 = Column(Boolean, default=False)
    created = Column(DateTime, default=datetime.utcnow)
    amount = Column(Numeric, nullable=False, unique=False)

    nonce = Column(INTEGER)
    gas = Column(INTEGER)
    gas_used = Column(INTEGER)
    gas_price = Column(BIGINT)
    fee = Column(Numeric)
    comment = Column(String(128))

    class Currency:
        USDT = 'USDT'
        TRX = 'TRX'

    def __repr__(self):
        return f'[Transaction {self.purpose} {self.currency.human_string(self.amount)} {self.from_address} → ' \
               f'{self.to_address} {self.time} {self.txid} status:{self.status}]'

    @staticmethod
    async def get_by_txid(session: AsyncSession, txid: str) -> Union['Transaction', None]:
        db_tx = await session.execute(
            select(Transaction).where(Transaction.txid == txid).options(
                selectinload(Transaction.currency)
            ))
        return db_tx.scalar()

    @staticmethod
    async def get_by_id(
            session: AsyncSession,
            id_: int
    ) -> Optional['Transaction']:
        db_tx = await session.execute(
            select(Transaction).where(Transaction.id == id_).options(
                selectinload(Transaction.currency)
            ))
        return db_tx.scalar()


class Cryptocurrency(BaseCurrency):
    """
    Внутренние валюты блокчейнов:
    BTC для BTC, ETH для ETH, BNB для BSC, TRX для Tron
    """
    __tablename__ = 'cryptocurrencies'

    decimals = Column(INTEGER, nullable=False, server_default=text('18'))

    name = Column(String(16), ForeignKey(Currency.name), primary_key=True)
    currency = relationship('Currency', back_populates='cryptocurrency')

