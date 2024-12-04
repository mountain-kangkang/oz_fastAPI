from fastapi import FastAPI, Query, Path

from item import router as item_router
from member import router as member_router
app = FastAPI()
app.include_router(item_router.router)
app.include_router(member_router.router)

@app.get("/")
def health_handler():
    return {"ping": "pong"}


# items = [
#     {"id": 1, "price":500, "name": "i_phone"},
#     {"id": 2, "price": 1000, "name": "galaxy"},
#     {"id": 3, "price": 2000, "name": "i-pad"},
# ]

# http://127.0.0.1/items
# http://127.0.0.1/items?max_price=10000
# http://127.0.0.1/items?max_price=10000&min_price=1000
# @app.get("/items/{item_id}")
# def item_handler(
#     # max_price: int | None = None,
#     # min_price: int | None = Query(default=None, gt=100, lte=10_000),
#     item_id: int = Path(default=..., gte=1, lt=1000),  # 1~999
# ):
#     for item in items:
#         if item["id"] == item_id:
#             return item
#     return None

# http://127.0.0.1:8000/items?q=foo&q=bar
# @app.get("/items")
# def item_handler(q: list = Query(default=[])):
#     return q if q else None