import asyncio
import time

# 코루틴(coroutine)
'''
    비동기적 실행 할 수 있는 함수
    중간에 코드 실행을 멈출 수 있음
    중간에 코드 실행을 멈출 수 있음 -> 대기 발생 -> 다른 작업
'''

async def async_function_1():
    print('async_function_1')
    print("sleeping")
    await asyncio.sleep(3)
    print('1_done')

async def async_function_2():
    print('async_function_2')
    print("sleeping")
    await asyncio.sleep(3)
    print('2_done')


async def main():
    start_time = time.time()
    coro1 = async_function_1()
    coro2 = async_function_2()
    await asyncio.gather(coro1, coro2)
    end_time = time.time()
    print(end_time - start_time)

asyncio.run(main())

# await를 사용하려면, await를 할 수 있는 대상에 대해서만 await 할 수 있음

# python 비동기 프로그래밍 할 때, 기억
# 1) async 키워드를 통해서 코루틴 만들어준다.
# 2) 대기가 발생하는 코드에서 await 붙여준다.
#   - await가 가능한 객체 앞에(비동기 라이브러리를 지원하는 코드)
#   - 코루틴 안에서