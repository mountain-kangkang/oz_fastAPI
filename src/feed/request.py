from pydantic import BaseModel


class PostCommentCreateRequestBody(BaseModel):
    content: str
    parent_id: int | None = None