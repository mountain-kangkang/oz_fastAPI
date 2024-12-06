import asyncio
import time
from datetime import datetime

import requests
from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from starlette.responses import JSONResponse

from item import router as item_router
from member import router as member_router
from member import router_async as member_async_router

app = FastAPI()
app.include_router(item_router.router)
app.include_router(member_router.router, prefix="/sync")
app.include_router(member_async_router.router, prefix="/async")

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request, exc):
    return JSONResponse(
        content={"error": exc.errors()[0]['msg']},
        status_code=status.HTTP_400_BAD_REQUEST,
    )

@app.exception_handler(ValueError)
def value_error_handler(request, exc):
    return JSONResponse(
        content={"error": str(exc)},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@app.get("/")
def health_handler():
    return {"ping": "pong"}

# @app.post("/images")
# def upload_image_handler(file: UploadFile):
#     return {
#         "filename": file.filename,
#         "content_type": file.content_type,
#         "file_size": file.size,
#     }


class NowResponse(BaseModel):
    now: datetime

@app.get(
    "/now",
    response_model=NowResponse,
    description="## 설명\n현재 시간을 반환하는 API입니다.",
    status_code=status.HTTP_200_OK,
)
def now_handler():
    # content = f"<html><body><h1>now: {datetime.now()}</h1></body></html>"
    # return HTMLResponse(content=content)
    return NowResponse(now=datetime.now())

# 정리
# FastAPI 는 기본적으로 비동기 프로그래밍이 적용되어 있음
# 일반적으로는 비동기 프로그램 안에서 동기 프로그램을 실행시키면 안됨
# 왜냐하면, 동기 코드가 event loop를 blocking 시켜버림

# 그런데 FastAPI는 동기 handler를 선언하더라도 비동기적으로 실행

# 조심해야되는건, async 붙인 비동기 handler를 선언했을 때는
# 그 안에서 동기 코드를 실행시키면 안 됨

# 잘 모르겠다 -> 전부 동기식으로 작성
# 난 좀 할 줄 안다 -> 전부 비동기식으로 작성
# 통일되어야 하는듯


# 서버에서 I/O 대기가 발생하는 경우
# 1) 외부 API 호출(ChatGPT, 크롤링, 소셜 로그인, ...)
# 2) 데이터베이스 통신 .commit()
# 3) 파일 다룰 때
# 4) 웹 소케(채팅, 푸시 알람, ...)

@app.get("/sync")
def sync_handler():
    # 1개 호출 : 0.6110383819996059
    # 3개 호출 : 1.6296170570003596
    # n개 호출 : 대략 0.6 * n
    start_time = time.perf_counter()
    urls = [
        "https://jsonplaceholder.typicode.com/posts",
        "https://jsonplaceholder.typicode.com/posts",
        "https://jsonplaceholder.typicode.com/posts",
    ]
    responses = []
    for url in urls:
        responses.append(requests.get(url))

    end_time = time.perf_counter()
    return {
        "duration": end_time - start_time,
        # "data": responses.json()
    }

import httpx
@app.get("/async")
async def async_handler():
    # 1개 호출: 0.8218387810002241
    # 3개 호출: 0.6380725449998863
    start_time = time.perf_counter()

    urls = [
        "https://jsonplaceholder.typicode.com/posts",
        "https://jsonplaceholder.typicode.com/posts",
        "https://jsonplaceholder.typicode.com/posts",
    ]

    async with httpx.AsyncClient() as client:
        tasks = []
        for url in urls:
            tasks.append(client.get(url))
        await asyncio.gather(*tasks)

    end_time = time.perf_counter()

    return {
        "duration": end_time - start_time,
        # "data": response.json()
    }