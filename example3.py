# time check

import asyncio
import time


async def f(delay):
    print("f1: ", delay)
    await asyncio.sleep(delay)
    print("f2: ", delay)

loop = asyncio.get_event_loop()
start = time.time()
t1 = loop.create_task(f(1))
t2 = loop.create_task(f(5))
t3 = loop.create_task(f(2))

# for data, n in [(t1, 1), (t2, 5), (t3, 2)]:
#     loop.run_until_complete(data)
#     print("for ", n)
print("-----")
loop.run_until_complete(t2)

loop.close()
end = time.time()
print(end - start)
