from datetime import datetime

from pydantic import BaseModel, ConfigDict

from feed.models import Post


class PostResponse(BaseModel):
    id: int
    image: str
    content: str
    created_at: datetime

    @classmethod
    def build(cls, post: Post):

        return cls(
            id=post.id,
            image=post.image_static_path,
            content=post.content,
            created_at=post.created_at,
        )


class PostBriefResponse(BaseModel):
    id: int
    image: str

    @classmethod
    def build(cls, post: Post):
        return cls(
            id=post.id,
            image=post.image_static_path,
        )

class PostListResponse(BaseModel):
    posts: list[PostBriefResponse]

    @classmethod
    def build(cls, posts: list[Post]):
        return cls(
            posts=[PostBriefResponse.build(post=p) for p in posts]
        )

class PostMemberResponse(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class PostDetailResponse(BaseModel):
    id: int
    image: str
    content: str
    created_at: datetime
    user: PostMemberResponse
    comments: "list[PostCommentResponse]"

    model_config = ConfigDict(from_attributes=True)

class PostCommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    content: str
    parent_id: int | None
    replies: "list[PostCommentResponse]"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)