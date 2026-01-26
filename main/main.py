from fastapi import FastAPI
from pathlib import Path
from fastapi.staticfiles import StaticFiles
#from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

from main.api import auth, team_management, tasks
from main.pattern import front_template

app = FastAPI()
#app.add_middleware(HTTPSRedirectMiddleware)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR))

app.include_router(auth.router)
app.include_router(team_management.router)
app.include_router(front_template.router)
app.include_router(tasks.router)
