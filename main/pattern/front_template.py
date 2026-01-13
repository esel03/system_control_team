from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter(prefix="")

@router.get("/")
def root():
    file_path = Path(__file__).parent / "templates" / "index.html"
    return FileResponse("main/templates/index.html")
