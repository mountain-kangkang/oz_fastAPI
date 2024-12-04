from pydantic import BaseModel


class UserMeResponse(BaseModel):        # 내 정보를 반환할 때
    username: str
    password: str


class UserResponse(BaseModel):
    username: str