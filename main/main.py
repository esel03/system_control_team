from fastapi import FastAPI
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import subprocess
import sys
import os

from main.api import auth, team_management, tasks
from main.pattern import front_template
from main.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Выполняется при старте приложения.
    Применяет миграции Alembic.
    """
    print("Запуск приложения")

    os.environ["DATABASE_URL"] = settings.get_db_url()
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),  # чтобы alembic.ini был найден
        )
        print("Миграции успешно применены")
        if result.stdout.strip():
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Ошибка при применении миграций")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        sys.exit(1)  # Останавливаем запуск
    except FileNotFoundError:
        print("Alembic не найден. Убедитесь, что он установлен (pip install alembic).")
        sys.exit(1)

    yield

    print("Приложение остановлено")

app = FastAPI(lifespan=lifespan)


STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR))

app.include_router(auth.router)
app.include_router(team_management.router)
app.include_router(front_template.router)
app.include_router(tasks.router)
