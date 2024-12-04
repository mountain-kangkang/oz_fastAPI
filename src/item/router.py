from fastapi import APIRouter

router = APIRouter(prefix="/item", tags=["Item"])

@router.get("")
def get_items_handler():
    return [
        {"id": 1, "name": "i_phone"},
        {"id": 2, "name": "galaxy"},
    ]