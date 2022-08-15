# 비동기 제너레이터

import asyncio
import time
# from aioredis import create_redis
#
#
# async def main():
#     redis = await create_redis(('localhost', 6379))
#     keys = ['Americas', 'Africa', 'Europe', 'Asia']
#
#     async for value in one_at_a_time(redis, keys):
#         await do_something_with(value)
#
#
# async def one_at_a_time(redis, keys):  # 코루틴 함수 & 비동기 제너레이터 함수
#     for k in keys:
#         value = await redis.get(k)
#         yield value

#-----


async def f(x):
    await asyncio.sleep(0.1)
    return x + 100


async def factory(n):
    for x in range(n):
        await asyncio.sleep(0.1)
        yield f, x


async def main():
    results = [await f(x) async for f, x in factory(3)]
    print('results = ', results)

start = time.time()
asyncio.run(main())
end = time.time()

print(end - start)
