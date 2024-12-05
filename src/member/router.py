from fastapi import APIRouter, Path, Body, status, HTTPException, Depends
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from sqlalchemy.orm import Session

from config.database import get_session
from member.authentication import check_password, encode_access_token, authenticate
from member.models import Member
from member.request import SignUpRequestBody
from member.response import UserMeResponse, UserResponse, JWTResponse

router = APIRouter(prefix="/members", tags=["Member"])


@router.post(
    "",
    response_model=UserMeResponse,
    status_code=status.HTTP_201_CREATED
)
def sign_up_handler(body: SignUpRequestBody, session: Session = Depends(get_session)):
    new_member = Member.create(
        username=body.username,
        password=body.password,
    )

    session.add(new_member)
    session.commit()

    return UserMeResponse(
        id=new_member.id,
        username=new_member.username,
        password=new_member.password,
    )

@router.post(
    "/login",
    response_model=JWTResponse,
    status_code=status.HTTP_200_OK
)
def login_handler(
    credentials: HTTPBasicCredentials = Depends(HTTPBasic()),
    session: Session = Depends(get_session),
):
    member: Member | None =session.query(Member).filter(Member.username == credentials.username).first()

    if member:
        if check_password(
                plain_text=credentials.password,
                hashed_password=member.password,
        ):
            return JWTResponse(access_token=encode_access_token(username=member.username))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Username or password incorrect",
    )

@router.get("/me")
def get_me_handler(
    username: str = Depends(authenticate),
    session: Session = Depends(get_session),
):
    member: Member | None = session.query(Member).filter(Member.username == username).first()

    if member:
        return UserMeResponse(
            id=member.id,
            username=member.username,
            password=member.password,
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
    username: str = Depends(authenticate),
    new_password: str = Body(..., embed=True),
    session: Session = Depends(get_session),
):
    member: Member | None = session.query(Member).filter(Member.username == username).first()

    if member:
        member.update_password(password=new_password)
        session.add(member)
        session.commit()

        return UserMeResponse(
            id=member.id,
            username=member.username,
            password=member.password,
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Username not found",
    )

@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def delete_user_handler(
    username: str = Depends(authenticate),
    session: Session = Depends(get_session),
):
    member: Member | None = session.query(Member).filter(Member.username == username).first()

    if member:
        session.delete(member)
        session.commit()
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
    session: Session = Depends(get_session),
):
    member: Member | None = session.query(Member).filter(
        Member.username == username,
    ).first()
    if member:
        return UserResponse(username=member.username)

    raise ValueError(f"User {username} not found")


