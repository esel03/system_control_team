from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/")
def get_items():
    return {"message": "List of items"}
