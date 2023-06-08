import asyncio

async def o():
    print(1)


async def t():
    print(2)


async def main():
    asyncio.create_task(o())
    asyncio.create_task(t())

asyncio.run(main())