from datetime import datetime

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from starlette.responses import JSONResponse

from item import router as item_router
from member import router as member_router
app = FastAPI()
app.include_router(item_router.router)
app.include_router(member_router.router)

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