from fastapi import APIRouter, Path
from pydantic import BaseModel, Field

router = APIRouter(prefix="/members", tags=["Member"])

db = [
    {
        "username": "admin",
        "password": "<PASSWORD>",
    },
    {
        "username": "user",
        "password": "<PASSWORD>",
    }
]

class SignUpRequestBody(BaseModel):
    username: str = Field(..., max_length=10)
    password: str

@router.get("")
def check_user():
    return db

@router.post("")
def sign_up_handler(body: SignUpRequestBody):
    db.append(
        {
            "username": body.username,
            "password": body.password,
        }
    )
    return db

@router.get("/{username}")
def get_user_handler(
        username: str = Path(..., max_length=10, min_length=1),
):
    for user in db:
        if user["username"] == username:
            return user
    return None