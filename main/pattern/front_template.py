from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(prefix="")


@router.get("/")
def root():
    return FileResponse("main/templates/index.html")
