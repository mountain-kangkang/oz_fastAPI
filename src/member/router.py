import time

from fastapi import APIRouter, Path, Body, status, HTTPException, Depends
from fastapi.security import HTTPBasicCredentials, HTTPBasic, HTTPAuthorizationCredentials, HTTPBearer

from member.authentication import hash_password, check_password, encode_access_token, JWTPayLoad, decode_access_token, \
    authenticate
from member.request import SignUpRequestBody, UserPasswordUpdateRequestBody
from member.response import UserMeResponse, UserResponse, JWTResponse

router = APIRouter(prefix="/members", tags=["Member"])

db = [
    {
        "username": "admin",    # asdf1357
        "password": "$2b$12$OXwX3CRVwHsrpcLZYmY3su.CNfpYFYBTj85MLuPC73lHBbCXKnahC",
    },
    {
        "username": "user",     # asdf1356
        "password": "$2b$12$QoOLqkT0Xr2cm34pUFKmHObj6ZeYA9snCdDtqxFyPr2IX3kUNANTK",
    }
]
# @router.get("")
# def check_user():
#     return db

@router.post(
    "",
    response_model=UserMeResponse,
    status_code=status.HTTP_201_CREATED
)
def sign_up_handler(body: SignUpRequestBody):
    new_user = {
        "username": body.username,
        "password": hash_password(plain_text=body.password),
    }
    db.append(new_user)

    return UserMeResponse(
        username=new_user["username"],
        password=new_user["password"],
    )

@router.post(
    "/login",
    response_model=JWTResponse,
    status_code=status.HTTP_200_OK
)
def login_handler(
     credentials: HTTPBasicCredentials = Depends(HTTPBasic()),
):
    for user in db:
        if user["username"] == credentials.username:
            if check_password(
                    plain_text=credentials.password,
                    hashed_password=user["password"]
            ):
                return JWTResponse(
                    access_token=encode_access_token(username=user["username"]),
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
            )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Username or password incorrect",
    )

    return

@router.get("/me")
def get_me_handler(
    auth_header: HTTPAuthorizationCredentials = Depends(authenticate)
):

    for user in db:
        if user["username"] == auth_header["username"]:
            return UserMeResponse(
                username=user["username"],
                password=user["password"],
            )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Username not found",
    )

@router.patch(
    "/me",
    response_model=UserMeResponse,
    status_code=status.HTTP_200_OK
)
def update_user_handler(
    credentials: HTTPBasicCredentials = Depends(HTTPBasic()),
    # body: UserPasswordUpdateRequestBody = Body(...),
    new_password: str = Body(..., embed=True),
):
    for user in db:
        if user["username"] == credentials.username:
            if check_password(plain_text=credentials.password, hashed_password=user["password"]):
                user["password"] = new_password
                return UserMeResponse(
                    username=user["username"],
                    password=user["password"],
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Username not found",
    )

@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=None,
)
def delete_user_handler(
    credentials: HTTPBasicCredentials = Depends(HTTPBasic()),
):
    for user in db:
        if user["username"] == credentials.username:
            db.remove(user)
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Username not found",
    )

@router.get(
    "/{username}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK
)
def get_user_handler(
    username: str = Path(..., max_length=10, min_length=1),
):
    for user in db:
        if user["username"] == username:
            return UserResponse(username=user["username"])

    raise ValueError(f"User {username} not found")


