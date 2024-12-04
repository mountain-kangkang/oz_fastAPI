from pydantic import BaseModel, Field


class SignUpRequestBody(BaseModel):
    username: str = Field(..., max_length=10)
    password: str


class UserPasswordUpdateRequestBody(BaseModel):
    new_password: str