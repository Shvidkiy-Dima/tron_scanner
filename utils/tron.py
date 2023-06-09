import asyncio
from settings import Config
from tronpy import AsyncTron
from aiohttp import ClientSession
from tronpy.providers.async_http import AsyncHTTPProvider
from tronpy.keys import PrivateKey


class TronAPI:
    # if you can find the transaction in the solidity node, then the transaction is guaranteed confirmed
    LAST_BLOCK = f'https://{Config.TRON_HOST}/walletsolidity/getnowblock'
    BLOCK_BY_NUM_RANGE = f'https://{Config.TRON_HOST}/walletsolidity/getblockbylimitnext'
    BLOCK_BY_NUM = f'https://{Config.TRON_HOST}/walletsolidity/getblockbynum'

    def __init__(self, api_key):
        self.api_key = api_key

        headers = {
                'Content-Type': "application/json",
            }

        if api_key:
            headers.update({'TRON-PRO-API-KEY': api_key})
        self._client: ClientSession = ClientSession(headers=headers)

    async def close_session(self):
        await self._client.close()

    async def _get_request(self, path, params=None):
        async with self._client.get(path, params=params) as resp:
            return await resp.json()

    async def _post_request(self, path, json_data=None):
        async with self._client.post(path, json=json_data) as resp:
            return await resp.json()

    async def get_last_block_num(self) -> int:
        while True:
            try:
                print(self.LAST_BLOCK)
                res = await self._get_request(self.LAST_BLOCK)
                return res['block_header']['raw_data']['number']
            except Exception:
                await asyncio.sleep(10)

    async def get_block_by_num(self, num: int) -> dict:
        res = await self._post_request(self.BLOCK_BY_NUM, json_data={"num": num})
        return res

    async def get_blocks_by_num_range(self, num: int, num_range=5) -> list:
        """
        Returns the list of Block Objects included in the 'Block Height' range specified. (Confirmed state)
        """
        res = await self._post_request(self.BLOCK_BY_NUM_RANGE, json_data={"startNum": num, "endNum": num + num_range})
        return res.get('block')

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()


class TronClient(AsyncTron):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, network=Config.NETWORK, **kwargs)
        self.provider = AsyncHTTPProvider(api_key=Config.API_KEY, endpoint_uri=Config.TRON_NODE)


async def send_trc20(from_address: str, to_address: str, amount: int, private_key: str, contract_address):
    async with TronClient() as client:
        contract = await client.get_contract(contract_address)
        txn = await contract.functions.transfer(to_address, amount)
        txn = txn.with_owner(from_address)
        txn = await txn.build()
        return await txn.sign(private_key).broadcast()
        # await txn.wait()


async def send_trx(from_address: str, to_address: str, amount: int, private_key: str) -> dict:
    async with TronClient() as client:
        print(amount, from_address, to_address)
        txn = client.trx.transfer(from_address, to_address, amount)
        txn = await txn.build()
        return await txn.sign(PrivateKey.fromhex(private_key)).broadcast()
       # await txn.wait()


async def get_balance(address: str, delay=1) -> int:
    for _ in range(100):
        try:
            async with TronClient() as client:
                return await client.get_account_balance(address)
        except Exception as e:
            print(e)
            await asyncio.sleep(delay*2)


async def get_trc20_balance(contract_address: str, address: str, delay=1) -> int:
    for _ in range(100):
        try:
            async with TronClient() as client:
                contract = await client.get_contract(contract_address)
                return await contract.functions.balanceOf(address)
        except Exception as e:
            print(e)
            await asyncio.sleep(delay*2)
