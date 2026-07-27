# System Control Team

Backend-сервис для управления комнатами, командами и задачами. Приложение
использует FastAPI, PostgreSQL/SQLAlchemy, Redis, JWT и Alembic.

## Возможности

- регистрация и OAuth2 password login;
- одноразовые refresh-токены с rotation через Redis;
- комнаты и команды с проверкой членства и роли руководителя;
- управление участниками без частичных bulk-операций;
- задачи с контролируемым жизненным циклом;
- статистика пользователя и команды;
- пагинация списков задач;
- liveness/readiness endpoints;
- структурированные production-логи и request ID.

## Локальный запуск

Требуются Python 3.13, PostgreSQL и Redis.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example main/.env
```

Отредактируйте `main/.env`, затем отдельно примените миграции:

```bash
./migrate.sh
./start.sh
```

Миграции намеренно не запускаются внутри web-процесса. В production
`./migrate.sh` должен выполняться release job до переключения трафика на новую
версию приложения.

Документация API доступна по адресу `http://localhost:8000/docs`.

## Основные endpoints

Все бизнес-endpoint'ы имеют префикс `/api/v1`.

- `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`;
- `GET /auth/me`;
- `POST|GET /rooms`;
- `GET|POST|DELETE /rooms/{room_id}/members`;
- `POST|GET /rooms/{room_id}/teams`;
- `GET|POST|DELETE /teams/{team_id}/members`;
- `POST|GET /teams/{team_id}/tasks`;
- `PATCH|DELETE /tasks/{task_id}`;
- `POST /tasks/{task_id}/complete`;
- `GET /teams/{team_id}/stats`;
- `GET /teams/{team_id}/users/{user_id}/stats`.

`GET /health/live` проверяет процесс, `/health/ready` — доступность PostgreSQL и
Redis.

## Модель прав

- участник комнаты может видеть комнату и её участников;
- руководитель комнаты добавляет/удаляет участников и создаёт команды;
- участник команды видит команду, её участников и задачи;
- руководитель команды управляет участниками и создаёт задачи;
- задачу изменяет её автор или руководитель;
- задачу завершает исполнитель или руководитель.

Удаление последнего руководителя комнаты или команды запрещено.

## Статические проверки

```bash
ruff check main alembic
black --check main alembic
python -m compileall -q main alembic
alembic heads
```

Автотесты пока не добавлены по решению владельца проекта. CI выполняет
компиляцию, lint/format checks, проверку графа миграций и уникальности FastAPI
маршрутов.

## Production

- задайте уникальный `SECRET_KEY` длиной не менее 32 символов;
- задайте точные `ALLOWED_HOSTS`, `CORS_ORIGINS` и список доверенных proxy;
- запускайте миграции отдельным release job;
- используйте TLS на ingress/reverse proxy;
- подключите `SENTRY_DSN` при необходимости;
- организуйте резервное копирование PostgreSQL и регулярную проверку
  восстановления;
- запускайте dependency audit в инфраструктурном security pipeline.
