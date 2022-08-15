# third party library
import asyncio
from asyncio import StreamReader, StreamWriter, gather
from collections import deque, defaultdict
from typing import Deque, DefaultDict

# 현재 연결된 구독자의 컬렉션으로 전역 변수이다. 클라이언트가 연결할 때마다. 구독하려는 채널 이름을 먼저 전송해야 한다. 채널 마다 하나의 덱에서 해당 채널에 대한 모든 구독자를 보유한다.
SUBSCRIBERS: DefaultDict[bytes, Deque] = defaultdict(deque)


async def client(reader: StreamReader, writer: StreamWriter):
    # client() 코루틴 함수는 새로운 연결 마다 수명이 긴 코루틴을 반환한다. main()에서 시작된 TCP 서버의 콜백으로 간주하자. 이번 줄에서 원격지의 호스트와 포트를 전달하였다.
    peername = writer.get_extra_info('peername')
    # 클라이언트의 프로토콜은 다음과 같다.
    #   - 처음 연결 시, 클라이언트는 구독할 채널 이름을 포함하는 메세지를 먼저 전송해야 한다. subscribe_chan 변수이다.
    #   - 그 후 연결을 유지하고 있는 동안, 클라이언트는 먼저 목적지 채널 이름을 포함하는 메세지를 먼저 전송한 후, 데이터를 포함하는 메세지를 전송한다. 브로커는 해당 채널 이름의 채널에 구독한 모든 클라이언트에게 데이터를 전달한다.
    subscribe_chan = await read_msg(reader)
    # StreamWriter 인스턴스를 전역 변수인 구독자 컬렉션에 추가한다.
    SUBSCRIBERS[subscribe_chan].append(writer)
    print(f'Remote {peername} subscribed to {subscribe_chan}')
    try:
        # 무한 루프로 클라이언트로부터 데이터를 기다린다. 클라이언트로부터 전달되는 천 번째 메세지는 목적지 채널 이름이어야 한다.
        while channel_name := await read_msg(reader):
            # 다음은 해당 채널로 배포할 실제 데이터가 전달된다.
            data = await read_msg(reader)
            print(f"Sending to {channel_name}: {data[:19]}...")
            # 목적지 채널에 대한 구독자들을 포함하는 덱을 얻는다.
            conns = SUBSCRIBERS[channel_name]
            # 채널 이름이 매직 워드인 /queue로 시작하는 경우, 특별한 처리를 한다. 구독자 중 단 하나에게만 데이터를 보낸다. 기족의 발행-구독 방식이 아니라 개별 클라이언트 간의 데이터 전달 방식이다.
            if conns and channel_name.startswith(b'/queue'):
                # 이것이 우리가 리스트가 아닌 덱을 사용한 이유이다. 덱을 순환시켜 /queue에 대한 데이터 전달 시 클라이언트들의 순서를 추적할 수 있다. 연산 비용이 비쌀 것으로 보일 수 있지만 한 번의 덱 순환은 O(1) 연산일 뿐이다.
                conns.rotate()
                # 첫 번째 클라언트를 대상으로 지정한다. 매 순환마다 바뀐다.
                conns = [conns[0]]
            # 각 클라이언트에게 메시지를 전달할 코루틴들의 리스트를 생성한 후 gather()에 풀어서 전달하고 모든 전송이 완료될 때까지 대기한다.
            await gather(*[send_msg(c, data) for c in conns])

    except asyncio.CancelledError:
        print(f"Remote {peername} closing connection.")
        writer.close()
        await writer.wait_closed()
    except asyncio.IncompleteReadError:
        print(f"Remote {peername} closing connection.")
        writer.close()
        await writer.wait_closed()
    finally:
        print(f"Remote {peername} disconnected")
        # client() 코루틴이 반환될 때 전역변수 SUBSCRIBERS에서 모든 클라이언트를 제거해야 한다. 안타깝게도 이 작업은 O(n) 연산으로 , n이 매우 크다면 좀 비싸질 것이다. 다른 데이터 구조를 사용하면 이를 해결할 수 있지만, 어차피 수명이 긴 연결이라는 가정 하에서 n이 그리 크지는 않을 것이고, 이 코드가 이해하기 쉬어서 그대로 두었다.
        SUBSCRIBERS[subscribe_chan].remove(writer)


async def read_msg(stream: StreamReader) -> bytes:
    size_bytes = await stream.readexactly(4)  # 처음 4바이트를 가져온다. 이는 페이로드의 크기이다.
    size = int.from_bytes(size_bytes, byteorder='big')  # 4 바이트를 정수로 변환한다.
    data = await stream.readexactly(size)  # 페이로드의 크기를 알고 있으므로, 스트림에서 그 크기만큼 읽는다.
    return data


async def send_msg(stream: StreamWriter, data: bytes):
    size_bytes = len(data).to_bytes(4, byteorder='big')
    stream.writelines([size_bytes, data])  # 쓰기는 읽기의 역순이다. 우선 데이터르이 크기를 4 바이트로 인코딩하여 전송하고, 데이터를 전송한다.
    await stream.drain()


async def main(*args, **kwargs):
    server = await asyncio.start_server(*args, **kwargs)
    async with server:
        await server.serve_forever()


try:
    asyncio.run(main(client, host='127.0.0.1', port=25000))
except KeyboardInterrupt:
    print("bye!")
