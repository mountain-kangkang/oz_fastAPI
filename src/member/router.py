from fastapi import APIRouter, Path, Body, status, HTTPException, Depends
from fastapi.security import HTTPBasicCredentials, HTTPBasic

from member.request import SignUpRequestBody, UserPasswordUpdateRequestBody
from member.response import UserMeResponse, UserResponse

router = APIRouter(prefix="/members", tags=["Member"])

db = [
    {
        "username": "admin",
        "password": "asdf1357",
    },
    {
        "username": "user",
        "password": "asdf1357",
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
        "password": body.password,
    }
    db.append(new_user)

    return UserMeResponse(
        username=new_user["username"],
        password=new_user["password"],
    )

@router.get("/me")
def get_me_handler(
        credentials: HTTPBasicCredentials = Depends(HTTPBasic())
):
    for user in db:
        if user["username"] == credentials.username:
            if user["password"] == credentials.password:
                return UserMeResponse(username=user["username"], password=user["password"])
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect password",
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
            if user["password"] != credentials.password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect password",
                )
            user["password"] = new_password
            return UserMeResponse(
                username=user["username"],
                password=user["password"],
            )

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





@router.delete("/{username}", status_code=status.HTTP_200_OK)
def delete_user_handler(
    username: str = Path(..., max_length=10),
):
    for user in db:
        if user["username"] == username:
            db.remove(user)
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Username not found",
    )