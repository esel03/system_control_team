# System Control Team

Backend-сервис для управления комнатами, командами, участниками и задачами.
Приложение построено на FastAPI и использует PostgreSQL, Redis, JWT и Alembic.

Основной способ локального запуска — Docker Compose. Он собирает приложение,
поднимает инфраструктуру, применяет миграции и запускает API в правильном
порядке.

## Возможности

- регистрация и авторизация через OAuth2 Password Flow;
- access- и одноразовые refresh-токены с ротацией через Redis;
- комнаты и команды с ролевой моделью доступа;
- управление участниками без частично выполненных bulk-операций;
- создание, изменение, завершение и удаление задач;
- фильтрация и пагинация списков задач;
- статистика по пользователям и командам;
- liveness- и readiness-проверки;
- request ID, структурированные production-логи и интеграция с Sentry.

## Стек

- Python 3.13;
- FastAPI и Uvicorn;
- PostgreSQL 16;
- SQLAlchemy 2 и Alembic;
- Redis 7;
- Pydantic Settings;
- Docker и Docker Compose.

## Быстрый старт

Понадобятся только Docker Engine и Docker Compose v2.

Соберите образы и запустите проект:

```bash
docker compose up --build
```

Для запуска в фоне:

```bash
docker compose up --build -d
```

После успешного старта доступны:

- API: `http://localhost:8000`;
- Swagger UI: `http://localhost:8000/docs`;
- ReDoc: `http://localhost:8000/redoc`;
- OpenAPI: `http://localhost:8000/openapi.json`;
- liveness: `http://localhost:8000/health/live`;
- readiness: `http://localhost:8000/health/ready`.

Проверить готовность приложения:

```bash
curl --fail http://localhost:8000/health/ready
```

При первом запуске Docker скачает базовые образы, соберёт приложение и создаст
volumes для данных. Это может занять несколько минут.

## Состав Docker Compose

| Сервис | Назначение | Доступ с хоста |
| --- | --- | --- |
| `api` | FastAPI-приложение | `127.0.0.1:8000` |
| `migrate` | Однократный запуск `alembic upgrade head` | не публикуется |
| `postgres` | Основная база данных | `127.0.0.1:5432` |
| `redis` | Refresh-токены и rate limiting | `127.0.0.1:6379` |

Порядок запуска контролируется healthcheck'ами:

1. PostgreSQL и Redis переходят в состояние `healthy`.
2. Сервис `migrate` применяет все миграции Alembic.
3. API запускается только после успешного завершения миграций.

Образ приложения собирается через multi-stage
[Dockerfile](./Dockerfile). Runtime-контейнер:

- работает под непривилегированным пользователем;
- использует read-only filesystem и отдельный временный `/tmp`;
- не получает Linux capabilities;
- корректно обрабатывает `SIGTERM`;
- содержит встроенный liveness healthcheck;
- не запускает миграции внутри web-процесса.

## Конфигурация

Compose имеет значения по умолчанию, достаточные для локального запуска.
Чтобы переопределить их, создайте файл `.env` в корне репозитория:

```dotenv
APP_HOST=127.0.0.1
APP_PORT=8000
POSTGRES_HOST_PORT=5432
REDIS_HOST_PORT=6379

DB_USER=system_control
DB_PASSWORD=replace-with-a-local-password
DB_NAME=system_control
SECRET_KEY=replace-with-a-secret-key-at-least-32-characters

ENVIRONMENT=development
SQL_ECHO=false
ALLOWED_HOSTS=localhost,127.0.0.1,api
CORS_ORIGINS=http://localhost:3000

MAX_REQUEST_BODY_BYTES=1048576
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=1
SENTRY_DSN=
```

Файл `.env` исключён из Git и Docker build context. Не добавляйте реальные
секреты в репозиторий.

Основные параметры:

| Переменная | Значение по умолчанию | Назначение |
| --- | --- | --- |
| `APP_HOST` | `127.0.0.1` | Интерфейс, на котором публикуется API |
| `APP_PORT` | `8000` | Порт API на хосте |
| `POSTGRES_HOST_PORT` | `5432` | Порт PostgreSQL на хосте |
| `REDIS_HOST_PORT` | `6379` | Порт Redis на хосте |
| `DB_USER` | `system_control` | Пользователь PostgreSQL |
| `DB_PASSWORD` | локальное значение Compose | Пароль PostgreSQL |
| `DB_NAME` | `system_control` | Имя базы данных |
| `SECRET_KEY` | локальное значение Compose | Ключ подписи JWT, минимум 32 символа |
| `ENVIRONMENT` | `development` | Окружение и формат логирования |
| `SQL_ECHO` | `false` | Вывод SQL-запросов в лог |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,api` | Разрешённые значения HTTP Host |
| `CORS_ORIGINS` | `http://localhost:3000` | Разрешённые CORS origins через запятую |
| `SENTRY_DSN` | пусто | Подключение отправки ошибок в Sentry |

Внутри Docker-сети приложение всегда использует `postgres:5432` и
`redis://redis:6379/0`. Переменные с суффиксом `_HOST_PORT` меняют только порты,
доступные на машине разработчика.

Значения `DB_PASSWORD` и `SECRET_KEY`, встроенные в Compose, предназначены
исключительно для локальной разработки.

## Управление окружением

Посмотреть состояние всех контейнеров, включая завершившийся `migrate`:

```bash
docker compose ps --all
```

Следить за логами API:

```bash
docker compose logs --follow --tail=200 api
```

Посмотреть логи миграций:

```bash
docker compose logs migrate
```

Пересобрать и перезапустить окружение после изменения исходного кода:

```bash
docker compose up --build -d
```

Исходники не подключены в контейнер как bind mount, поэтому после изменения
кода образ необходимо пересобрать.

Запустить миграции вручную:

```bash
docker compose run --rm migrate
```

Открыть PostgreSQL CLI с настройками по умолчанию:

```bash
docker compose exec postgres psql -U system_control -d system_control
```

Проверить Redis:

```bash
docker compose exec redis redis-cli ping
```

Проверить итоговую конфигурацию Compose без запуска контейнеров:

```bash
docker compose config --quiet
```

Остановить окружение, сохранив данные:

```bash
docker compose down
```

Полностью удалить контейнеры и локальные данные PostgreSQL и Redis:

```bash
docker compose down --volumes --remove-orphans
```

Последняя команда необратимо удаляет содержимое локальных volumes.

## Данные

PostgreSQL и Redis используют именованные volumes:

- `postgres_data` — таблицы и служебные данные PostgreSQL;
- `redis_data` — AOF и снимки Redis.

Обычный `docker compose down` не удаляет эти данные. При следующем запуске
окружение продолжит использовать существующие volumes.

Если были изменены `DB_USER`, `DB_PASSWORD` или `DB_NAME`, но volume PostgreSQL
уже существует, новые значения не переинициализируют базу. Для чистого
локального запуска удалите volumes и поднимите окружение заново.

## API

Все бизнес-endpoints имеют префикс `/api/v1`.

### Авторизация

- `POST /api/v1/auth/register`;
- `POST /api/v1/auth/login`;
- `POST /api/v1/auth/refresh`;
- `POST /api/v1/auth/logout`;
- `GET /api/v1/auth/me`.

Endpoint входа принимает OAuth2 form data. Для защищённых запросов передавайте
access-токен:

```http
Authorization: Bearer <access-token>
```

### Комнаты и команды

- `POST|GET /api/v1/rooms`;
- `GET|POST|DELETE /api/v1/rooms/{room_id}/members`;
- `POST|GET /api/v1/rooms/{room_id}/teams`;
- `GET|POST|DELETE /api/v1/teams/{team_id}/members`.

### Задачи и статистика

- `POST|GET /api/v1/teams/{team_id}/tasks`;
- `PATCH|DELETE /api/v1/tasks/{task_id}`;
- `POST /api/v1/tasks/{task_id}/complete`;
- `GET /api/v1/teams/{team_id}/users/{user_id}/tasks`;
- `GET /api/v1/teams/{team_id}/stats`;
- `GET /api/v1/teams/{team_id}/users/{user_id}/stats`.

Актуальные форматы запросов, ответов и коды ошибок доступны в Swagger UI.

## Модель доступа

- участник комнаты может просматривать комнату и её участников;
- руководитель комнаты добавляет и удаляет участников, создаёт команды;
- участник команды видит команду, её участников и задачи;
- руководитель команды управляет участниками и создаёт задачи;
- задачу может изменить или удалить её автор либо руководитель;
- задачу может завершить исполнитель или руководитель;
- удалить последнего руководителя комнаты или команды нельзя.

## Структура проекта

```text
main/
├── api/           # FastAPI routers и зависимости
├── db/            # подключение к БД и SQLAlchemy-модели
├── repositories/  # операции с хранилищами
├── schemas/       # Pydantic-схемы
├── services/      # бизнес-логика
├── config.py      # настройки приложения
└── main.py        # создание FastAPI-приложения
alembic/           # миграции базы данных
Dockerfile         # сборка runtime-образа
compose.yml        # локальное окружение
start.sh           # запуск Uvicorn
migrate.sh         # применение миграций Alembic
```

## Production

Текущий Compose-файл рассчитан на локальную разработку. Перед production
развёртыванием необходимо:

- хранить `SECRET_KEY`, пароли и `SENTRY_DSN` в менеджере секретов;
- задать уникальный `SECRET_KEY` длиной не менее 32 символов;
- использовать точные `ALLOWED_HOSTS`, `CORS_ORIGINS` и доверенные proxy;
- запускать миграции отдельным release job до переключения трафика;
- использовать TLS на ingress или reverse proxy;
- не публиковать PostgreSQL и Redis наружу;
- настроить аутентификацию, резервное копирование и мониторинг хранилищ;
- закрепить версии или digest базовых Docker-образов;
- настроить централизованные логи, метрики и оповещения;
- регулярно проверять восстановление PostgreSQL из резервной копии.
