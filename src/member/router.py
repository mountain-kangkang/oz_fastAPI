import asyncio
from fastapi import APIRouter, Path, Body, status, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from pydantic import constr
from sqlalchemy.orm import Session

from config.cache import redis_client
from config.database.connection import get_session
from member.authentication import check_password, encode_access_token, authenticate
from member.email_service import send_otp
from member.models import Member
from member.otp_service import create_otp
from member.repository import MemberRepository
from member.request import SignUpRequestBody
from member.response import UserMeResponse, UserResponse, JWTResponse

router = APIRouter(prefix="/members", tags=["SnycMember"])


@router.post(
    "",
    response_model=UserMeResponse,
    status_code=status.HTTP_201_CREATED
)
async def sign_up_handler(
    body: SignUpRequestBody,
    background_tasks: BackgroundTasks,
    # session: Session = Depends(get_session),
    member_repo: MemberRepository = Depends(),
    # == member_repo: MemberRepository = Depends(MemberRepository),
):
    new_member = Member.create(
        username=body.username,
        password=body.password,
    )
    member_repo.save(new_member)
    background_tasks.add_task(
        send_welcome_email, username=new_member.username
    )

    return UserMeResponse.model_validate(obj=new_member)

async def send_welcome_email(username):
    await asyncio.sleep(5)
    print(f"{username}님 회원가입을 환영합니다!")

@router.post(
    "/login",
    response_model=JWTResponse,
    status_code=status.HTTP_200_OK
)
def login_handler(
    credentials: HTTPBasicCredentials = Depends(HTTPBasic()),
    # session: Session = Depends(get_session),
    member_repo: MemberRepository = Depends(),
):
    # member: Member | None = member_repo.get_member_by_username(username=credentials.username)

    if member:= member_repo.get_member_by_username(username=credentials.username):
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

# OTP 발급 API(POST /members/email/otp)
# 1) 이미 회원가입한 사용자가 이메일 인증을 위해 이메일 주소 입력
# 2) 해당 이메일 주소로 OTP 코드(6자리 숫자) 발송
# 3) 3분 TTL을 걸고 OTP를 Redis 저장
@router.post(
    "/email/otp",
    status_code=status.HTTP_200_OK,
)
def create_email_otp_handler(
        background_tasks: BackgroundTasks,
        username: str = Depends(authenticate),
        email: str = Body(
            ...,
            pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
            embed=True,
            examples=["string@example.com"],
        ),
        member_repo: MemberRepository = Depends(),
):
    # 1) 3분 TTL을 걸고 OTP를 Redis 저장
    if not (member := member_repo.get_member_by_username(username=username)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 2) 해당 이메일 주소로 OTP 코드(6자리 숫자) 발송
    otp: int = create_otp()
    # redis_client.setex(f"members:{member.id}:email:otp", 3*60, otp)
    cache_key: str = f"members:{member.id}:email:otp"
    redis_client.hset(
        name=cache_key,
        mapping={"otp": otp, "email": email},
    )
    redis_client.expire(cache_key, 3* 60)

    # 3) 해당 이메일 주소로 OTP 코드(6자리 숫자) 발송
    background_tasks.add_task(
        send_otp, email=email, otp=otp,
    )

    return {"detail": "Success"}

# OTP 인증 API(POST /member/email/otp/verify
# 1) 사용자가 이메일로 받은 OTP를 서버에 전달
# 2) OTP를 검증(Redis에서 조회)
@router.post("email/otp/verify")
def verify_email_otp_handler(
    username: str = Depends(authenticate),
    otp: int = Body(..., embed=True, ge=100_000, le=999_999),
    member_repo: MemberRepository = Depends(),
):
    if not (member := member_repo.get_member_by_username(username=username)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    cached_data = redis_client.hgetall(f"members:{member.id}:email:otp")
    if not (cached_otp := cached_data.get("otp")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP not found",
        )

    if otp != int(cached_otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP mismatch",
        )

    email: str = cached_data.get("email")
    member.update_email(email=email)
    member_repo.save(member=member)
    return UserMeResponse.model_validate(obj=member)

@router.get("/me")
def get_me_handler(
    username: str = Depends(authenticate),
    # session: Session = Depends(get_session),
    member_repo: MemberRepository = Depends(),
):
    # member: Member | None = member_repo.get_member_by_username(username=username)

    if member:= member_repo.get_member_by_username(username=username):
        return UserMeResponse.model_validate(obj=member)

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
    # session: Session = Depends(get_session),
    member_repo: MemberRepository = Depends(),
):
    # member: Member | None = member_repo.get_member_by_username(username=username)

    if member := member_repo.get_member_by_username(username=username):
        member.update_password(password=new_password)
        member_repo.save(member)

        return UserMeResponse.model_validate(obj=member)

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
    # session: Session = Depends(get_session),
    member_repo: MemberRepository = Depends(),
):
    # member: Member | None = session.query(Member).filter(Member.username == username).first()

    if member := member_repo.get_member_by_username(username=username):
        member_repo.delete(member)
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


