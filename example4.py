# run_in_executor test
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor as Executor


# async def main():
#     loop = asyncio.get_running_loop()
#     future = loop.run_in_executor(None, blocking)
#     try:
#         print(f"{time.ctime()} Hello from a thread")
#         await asyncio.sleep(1.0)
#         print(f"{time.ctime()} goodbye!")
#     finally:
#         await future
#
# ------ 위 방법은 한계점이 있다. 익스큐터 작업을 생성하는 영역 마다 try/finally를 사용한다. 비동기 태스크를 생성하듯이 익스큐터 작업을 만들고 asyncio.run()으로 처리하여 부드럽게 프로그램을 종료하는 방식이 더 낫다.

async def make_coro(future):
    print("start")
    try:
        return await future
    except asyncio.CancelledError:
        return await future


async def main():
    loop = asyncio.get_running_loop()
    future = loop.run_in_executor(None, blocking)
    asyncio.create_task(make_coro(future))  # 퓨처를 감싸 태스크로 만들었기 때문에 asyncio.run()의 종료 절차 중에 all_tasks() 를 통해 얻는 태스크 목록에 포함되어 cancel() 메서드가 호출될 수 있다.
    print(f'{time.ctime()} Hello!')
    print(f'{time.ctime()} goodbye!')
    await asyncio.sleep(1.0)


def blocking():
    time.sleep(2.0)
    print(f"{time.ctime()} Hello from a thread")


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("bye!")
