from datetime import datetime

from pydantic import BaseModel, ConfigDict

from feed.models import Post


class PostResponse(BaseModel):
    id: int
    image: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PostBriefResponse(BaseModel):
    id: int
    image: str

    @classmethod
    def build(cls, post: Post):
        filename: str = post.image.split("/")[-1]
        return cls(
            id=post.id,
            image=f"http://127.0.0.1:8000/static/{filename}",
        )

class PostListResponse(BaseModel):
    posts: list[PostBriefResponse]

    @classmethod
    def build(cls, posts: list[Post]):
        return cls(
            posts=[PostBriefResponse.build(post=p) for p in posts]
        )
