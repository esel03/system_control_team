#!/bin/bash

# Применяем миграции к базе данных
echo "Запуск миграций Alembic..."
alembic upgrade head

# Проверяем, успешно ли прошли миграции
if [ $? -ne 0 ]; then
    echo "Ошибка при выполнении миграций"
    exit 1
fi

echo "Миграции успешно применены"

# Запуск FastAPI-приложения через uvicorn
echo "Запуск приложения..."
uvicorn main.main:app --host 0.0.0.0 --port 8000 --reload
