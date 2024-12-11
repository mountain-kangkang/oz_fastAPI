from fastapi import APIRouter, Path, Body, status, HTTPException, Depends
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.database.connection_async import get_async_session
from member.service.authentication import check_password, encode_access_token, authenticate
from member.models import Member
from member.schema.request import SignUpRequestBody
from member.schema.response import UserMeResponse, UserResponse, JWTResponse

router = APIRouter(prefix="/members", tags=["AsyncMember"])


@router.post(
    "",
    response_model=UserMeResponse,
    status_code=status.HTTP_201_CREATED
)
async def sign_up_handler(body: SignUpRequestBody, session: AsyncSession = Depends(get_async_session)):
    new_member = Member.create(
        username=body.username,
        password=body.password,
    )

    session.add(new_member)
    await session.commit()

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
async def login_handler(
    credentials: HTTPBasicCredentials = Depends(HTTPBasic()),
    session: AsyncSession = Depends(get_async_session),
):
    # 1) DB에서 데이터 조회 -> I/O 발생
    result = await session.execute(
        select(Member).filter(Member.username == credentials.username)
    )
    # 2) FastAPI 서버 상에서
    member: Member | None = result.scalars().first()
    # await -> I/O 대기가 발생하는 순간 = DB랑 실제로 통신하는 수간
    # .close() / .commit()

    # ORM 데이터를 조회하는 것은
    # 1) DB랑 통신
    # 2) sqlalchemy DB에서 가져온 데이터를 member 객체로 변환

    if member:
        if check_password(
                plain_text=credentials.password,
                hashed_password=member.password,
        ):
            return JWTResponse(access_token=encode_access_token(user_id=member.id))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Username or password incorrect",
    )

@router.get("/me")
async def get_me_handler(
    user_id: int = Depends(authenticate),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Member).filter(Member.id == user_id)
    )
    member: Member | None = result.scalars().first()

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
async def update_user_handler(
    user_id: int = Depends(authenticate),
    new_password: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Member).filter(Member.id == user_id)
    )
    member: Member | None = result.scalars().first()

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
async def delete_user_handler(
    user_id: int = Depends(authenticate),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Member).filter(Member.id == user_id)
    )
    member: Member | None = result.scalars().first()

    if member:
        await session.delete(member)
        await session.commit()
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
async def get_user_handler(
    username: str = Path(..., max_length=10, min_length=1),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Member).filter(Member.username == username)
    )
    member: Member | None = result.scalars().first()
    if member:
        return UserResponse(username=member.username)

    raise ValueError(f"User {username} not found")


