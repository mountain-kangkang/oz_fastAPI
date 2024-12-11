import asyncio

import httpx
from fastapi import APIRouter, Path, Body, status, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse

from config import settings
from config.cache import redis_client
from config.database.connection import get_session
from member.service.authentication import check_password, encode_access_token, authenticate
from member.service.email_service import send_otp
from member.models import Member, SocialProvider
from member.service.otp_service import create_otp
from member.repository import MemberRepository
from member.schema.request import SignUpRequestBody
from member.schema.response import UserMeResponse, UserResponse, JWTResponse

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
            return JWTResponse(access_token=encode_access_token(user_id=member.id))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Username or password incorrect",
    )

# 1) kakao 로그인 API
# 사용자가 카카오 로그인 하려고 할 때
# 사용자를 카카오 redirect => kakao에서 동의화면 보여줌
@router.get(
    "/social/kakao/login",
    status_code=status.HTTP_200_OK,
)
def kakao_social_login_handler():
    return RedirectResponse(
        url="https://kauth.kakao.com/oauth/authorize"
            f"?client_id={settings.kakao_rest_api_key}"
            f"&redirect_uri={settings.kakao_redirect_url}"
            f"&response_type=code",     # callback: authrization_code
    )


# 2) kakao callback API : 사용자의 인증 동의 후 kakao에서 사용자의 auth_code를 return
@router.get(
    "/social/kakao/callback",
    status_code=status.HTTP_200_OK,
)
def kakao_social_callback_handler(
    code: str,
    member_repo: MemberRepository = Depends(),
):
    # 1) path parameter
    # /members/social/kakao/callback/{abc} -> auth_code: abc

    # 2) query parameter
    # GET /members/social/kakao/callback?auth_code=abc
        # 1) auth_code -> access_token 발급받기
    response = httpx.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": settings.kakao_rest_api_key,
            "redirect_uri": settings.kakao_redirect_url,
            "code": code,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
    )

    response.raise_for_status()
    if response.is_success:
        # 2) access_token -> 사용자 정보 조회
        access_token: str = response.json().get("access_token")

        profile_response = httpx.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        profile_response.raise_for_status()
        if profile_response.is_success:
            # 3) 사용자 정보 -> 회원가입/로그인
            member_profile: dict = profile_response.json()
            member_subject: str = str(member_profile["id"])

            email: str = profile_response.json()["kakao_account"]["email"]
            member: Member | None = member_repo.get_member_by_social_email(
                social_provider=SocialProvider.KAKAO,
                email=email
            )

            if member:  # 이미 가입된 사용자 -> 로그인
                return JWTResponse(access_token=encode_access_token(user_id=member.id))
            # 처음 소셜 로그인하는 사용자
            new_member = Member.social_signup(
                social_provider=SocialProvider.KAKAO,
                subject=member_subject,
                email=email,
            )
            member_repo.save(new_member)

            return JWTResponse(
                access_token=encode_access_token(user_id=new_member.id),
            )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Kakao social login failed",
    )
        # 4) JWT 반환

    # 3) request body
    # autu_code: UserMeRequest

    # 4) header



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
        user_id: int = Depends(authenticate),
        email: str = Body(
            ...,
            pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
            embed=True,
            examples=["string@example.com"],
        ),
        member_repo: MemberRepository = Depends(),
):
    # 1) 3분 TTL을 걸고 OTP를 Redis 저장
    if not (member := member_repo.get_member_by_id(user_id=user_id)):
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
    user_id: int = Depends(authenticate),
    otp: int = Body(..., embed=True, ge=100_000, le=999_999),
    member_repo: MemberRepository = Depends(),
):
    if not (member := member_repo.get_member_by_id(user_id=user_id)):
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
    user_id: int = Depends(authenticate),
    # session: Session = Depends(get_session),
    member_repo: MemberRepository = Depends(),
):
    # member: Member | None = member_repo.get_member_by_username(username=username)

    if member:= member_repo.get_member_by_id(user_id=user_id):
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
    user_id: int = Depends(authenticate),
    new_password: str = Body(..., embed=True),
    # session: Session = Depends(get_session),
    member_repo: MemberRepository = Depends(),
):
    # member: Member | None = member_repo.get_member_by_username(username=username)

    if member := member_repo.get_member_by_id(user_id=user_id):
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
    user_id: int = Depends(authenticate),
    # session: Session = Depends(get_session),
    member_repo: MemberRepository = Depends(),
):
    # member: Member | None = session.query(Member).filter(Member.username == username).first()

    if member := member_repo.get_member_by_id(user_id=user_id):
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
    member_repo: MemberRepository = Depends(),
):

    member: Member | None = member_repo.get_member_by_username(username=username)
    if member:
        return UserResponse(username=member.username)

    raise ValueError(f"User {username} not found")


