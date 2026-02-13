import asyncio


async def print1():  # функция-корутина
    print(1)


async def print2():
    await asyncio.sleep(2)
    print(2)


async def print3():
    print(3)


async def main():
    tasks = [
        asyncio.create_task(print1()),
        asyncio.create_task(print2()),
        asyncio.create_task(print3()),
    ]
    await asyncio.gather(*tasks)  # с версии 3.10


# async def main(): # это с 3.11
#     async with asyncio.TaskGroup() as tg:
#         tg.create_task(print1())
#         tg.create_task(print2())
#         tg.create_task(print3())


asyncio.run(main())
