import logging
from dataclasses import dataclass
from datetime import timedelta, timezone, datetime
from decimal import Decimal
from typing import Optional

from tronpy.keys import to_base58check_address

from models import Transaction
from models import Currency, AsyncSession
from utils.transfer_data_decoder import decode_transfer

logger = logging.getLogger()


@dataclass
class TransactionSchema:
    amount: Decimal
    from_address: str  # base
    to_address: str  # base
    currency_name: str
    tx_id: str
    time: int
    trc20: bool
    contract_address: str = None


def get_correct_data(data: str):
    data = data[8:]
    data = data.replace('41', '00', 1)
    return bytes.fromhex(data)


def is_transfer(data, transactionFuncId='a9059cbb'):
    func = data[:8]
    return func == transactionFuncId


def _is_success_tx(tx: dict):
    try:
        return tx['ret'][0]["contractRet"] == 'SUCCESS'
    except Exception:
        logger.error('error is success')
        return False


def _parse_transfer(data) -> (str, int):
    try:
        # data = get_correct_data(data)
        # address, value = trx_abi.decode_abi(['address', 'uint256'], data)
        # address = to_hex_address(address)
        return decode_transfer(data)
    except Exception as e:
        logger.exception(f"err parse transfer: {e}")
        return None, None


def _parse_tx(tx, contracts):
    # Только входящие TRX или USDT - transfer()
    contr = tx["raw_data"]['contract'][0]

    if contr['type'] == "TransferContract":
        # TRX transfer
        to_address = contr['parameter']['value']['to_address']
        from_address = contr['parameter']['value']['owner_address']
        amount = to_decimal(contr['parameter']['value']['amount'], 6)
        if amount < Decimal(0.1):
            return None, None
        currency_name = Transaction.Currency.TRX
        contract_address = None
        trc20 = False

    elif contr['type'] == "TriggerSmartContract":

        contract_address = tx['raw_data']["contract"][0]["parameter"]["value"]['contract_address']
        contract_address = to_base58check_address(contract_address)

        if contract_address not in contracts.keys():
            return None, None

        contr_data = tx['raw_data']["contract"][0]["parameter"]["value"]["data"]

        if not is_transfer(contr_data):
            return None, None

        to_address, value = _parse_transfer(contr_data)
        if to_address is None or value is None:
            logger.error(f"tx with invalid data - {tx['txID']}")
            return None, None

        amount = to_decimal(value, int(contracts[contract_address]['dec']))
        from_address = tx['raw_data']["contract"][0]["parameter"]["value"]['owner_address']
        to_address = to_address
        currency_name = contracts[contract_address]['name']
        trc20 = True

    else:
        return None, None

    timestamp = tx['raw_data'].get("timestamp")
    to_address = to_base58check_address(to_address)
    from_address = to_base58check_address(from_address)

    tx_schema = TransactionSchema(tx_id=tx['txID'], time=timestamp / 1000 if (timestamp is not None) else None,
                                  to_address=to_address, from_address=from_address,
                                  amount=amount, currency_name=currency_name, trc20=trc20,
                                  contract_address=contract_address)

    return to_address, tx_schema


def parse_txs(txs: list, wallets, contracts):
    ret = []
    txs = [tx for tx in txs if _is_success_tx(tx)]

    for tx in txs:

        to_addr, data = _parse_tx(tx, contracts)
        to_addr = to_base58check_address(to_addr) if to_addr else None
        if not to_addr or not data or to_addr not in wallets:
            continue

        ret.append(data)

    return ret


def format_date(timestamp):
    try:
        return datetime.fromtimestamp(timestamp).replace(tzinfo=timezone(timedelta(hours=3)))
    except Exception:
        return None




def to_decimal(value, decimals: int) -> Decimal:
    d = Decimal(value).scaleb(-decimals)
    return Decimal(round(d, decimals))
