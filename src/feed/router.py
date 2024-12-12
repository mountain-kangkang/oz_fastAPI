import os
import shutil
import uuid

from fastapi import APIRouter, status, Depends, UploadFile, File, Form, Body, HTTPException
from sqlalchemy.exc import IntegrityError
from starlette.responses import JSONResponse

from feed.models import Post, PostComment, PostLike
from feed.repository import PostRepository, PostCommentRepository, PostLikeRepository
from feed.request import PostCommentCreateRequestBody
from feed.response import PostResponse, PostListResponse, PostCommentResponse, PostDetailResponse, PostLikeResponse
from member.models import Member
from member.repository import MemberRepository
from member.service.authentication import authenticate

router = APIRouter(tags=["Feed"])

# 1) Post 생성하기
# POST /posts
@router.post(
    "/posts",
    status_code=status.HTTP_201_CREATED,
    response_model=PostResponse,
)
def create_post_handler(
    user_id: int = Depends(authenticate),
    image: UploadFile = File(...),      # Content-Type : multipart/form-data
    content:str = Form(),
    post_repo: PostRepository = Depends(),
):

    # 1) image를 로컬 서버에 저장
    image_filename: str = f"{uuid.uuid4()}_{image.filename}"
    file_path = os.path.join("feed/posts", image_filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(image.file, f)

    # 2) image의 경로 & content -> Post 테이블에 저장
    new_post = Post.create(
        user_id=user_id,
        content=content,
        image=file_path,
    )
    try:
        post_repo.save(new_post)
    except IntegrityError:
        # JWT 안에 user_id가 남아있지만, 실제로 user는 db에서 삭제된 경우
        # (IntergrigyError = 데이터 무결성이 훼손된 경우)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not exist"
        )
    return PostResponse.build(post=new_post)

# 2) Feed 조회(전체 Post 조회)
@router.get(
    "/posts",
    status_code=status.HTTP_200_OK,
    response_model=PostListResponse,
)
def get_posts_handler(
    post_repo: PostRepository = Depends(),
):
    # 1) 전체 post 조회(created_at 역순) => 최신 게시글 순서대로
    posts = post_repo.get_posts()
    # 2) 그대로 반환

    return PostListResponse.build(posts=posts)

# 5) Post 상세 조회
#   - image, user, like_count, comment_count
@router.get(
    "/posts/{post_id}",
    status_code=status.HTTP_200_OK,
    response_model=PostDetailResponse,
)
def get_post_handler(
    post_id: int,
    post_repo: PostRepository = Depends(),
):
    if not (post := post_repo.get_post_detail(post_id=post_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post does not exist"
        )

    return PostDetailResponse.model_validate(obj=post)

# 3) Post 수정
@router.patch(
    "/posts/{post_id}",
    status_code=status.HTTP_200_OK,
    response_model=PostResponse,
)
def update_post_handler(
    post_id: int,
    user_id: int = Depends(authenticate),
    contest: str = Body(..., embed=True),
    post_repo: PostRepository = Depends(),
):
    # 1) Post 조회, 없으면 404
    if not (post := post_repo.get_post(post_id=post_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post does not exist",
        )

    if post.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this post",
        )

    # 2) Post update(content)
    post.update_content(content=contest)
    post_repo.save(post=post)

    return PostResponse.build(post=post)

# 4) Post 삭제
@router.delete(
    "/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def delete_post_handler(
    post_id: int,
    user_id: int = Depends(authenticate),
    post_repo: PostRepository = Depends(),
):
    ### 방법 1번
    # 장점: 클라이언트가 정확한 에러상황을 인지하기 쉬움
    # 단점: 쿼리가 2번 발생, 코드가 길어짐

    #1 post 조회, 없으면 404
    if not (post := post_repo.get_post(post_id=post_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post does not exist",
        )

    #2 있으면 삭제
    if post.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this post",
        )

    post_repo.delete(post)

    ###방법 2
    # 장점: 데이터베이스에 쿼리를 1번만 실행, 코드가 짧음
    # 단점: 클라이언트가 정확한 상황에 대하여 인지하기 어려움
    # post_repo.delete_my_post(user_id=user_id, post_id=post_id)


# 6) Post 댓글 작성
@router.post(
    "/posts/{post_id}/comments",
    status_code=status.HTTP_201_CREATED,
)
def create_comment_handler(
    post_id: int,
    user_id: int = Depends(authenticate),   # 로그인한 사용자만 댓글 가능
    body: PostCommentCreateRequestBody = Body(...),
    post_repo: PostRepository = Depends(),
    comment_repo: PostCommentRepository = Depends(),
):
    # post 조회
    if not (post := post_repo.get_post(post_id=post_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post does not exist",
        )

    # parent_id가 있으면 검증
    if body.parent_id:
        parent_comment = comment_repo.get_comment(comment_id=body.parent_id)
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent Comment does not exist",
            )

        if parent_comment.post_id != post.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent comment & Post not match",
            )

        # parent_comment가 이미 대댓이라면 댓글 추가 X
        if not parent_comment.is_parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="대댓글에는 댓글을 달 수 없습니다.",
            )

    new_comment = PostComment.create(
        user_id=user_id,
        post_id=post_id,
        content=body.content,
        parent_id=body.parent_id,
    )
    comment_repo.save(comment=new_comment)

    return PostCommentResponse.model_validate(obj=new_comment)

# 8) Post 좋아요
@router.post(
    "/posts/{post_id}/like",
    status_code=status.HTTP_201_CREATED,
    response_model=PostLikeResponse,
)
def like_post_handler(
    post_id: int,
    user_id: int = Depends(authenticate),
    like_repo: PostLikeRepository = Depends(),
):
    like = PostLike.create(user_id=user_id, post_id=post_id)
    try:
        like_repo.save(like=like)
    except IntegrityError:
        like_repo.rollback()
        like = like_repo.get_like_by_user(user_id=user_id, post_id=post_id)

    # 1) like 성공한 경우
        # 서버 상에서 PostLike() 생성
        # .save() -> DB에 저장
        # post_like.id, post_like.create_at 할당

    # 2) 실패한 경우(400 error)
        # 서버 상에서 PostLike() 생성
        # .save() -> DB 저장 실패(IntegrityError)
        # post_like.id, post_like.create_at 할당 실패

    return PostLikeResponse.model_validate(obj=like)

# 9) Post 좋아요 취소
@router.delete(
    "/posts/{post_id}/like",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def cancel_post_like_handler(
        post_id: int,
        user_id: int = Depends(authenticate),
        like_repo: PostLikeRepository = Depends(),
):
    like_repo.delete_like_by_user(user_id=user_id, post_id=post_id)

# 7) Post 댓글 삭제
@router.delete(
    "/comment/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_comment_handler(
        comment_id: int,
        user_id: int = Depends(authenticate),
        comment_repo: PostCommentRepository = Depends(),
):
    if not (comment := comment_repo.get_comment(comment_id=comment_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment does not exist",
        )

    if comment.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this comment",
        )

    comment_repo.delete(comment=comment)

