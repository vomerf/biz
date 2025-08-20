О проекте

Это простой бэкенд-сервис на Python с использованием FastAPI и SQLAlchemy. В проекте:
```
Модель героя с характеристиками: имя, интеллект, сила, скорость, мощь.
Фильтрация героев по различным параметрам.
Асинхронная работа с базой данных PostgreSQL.
Миграции базы данных через Alembic.
Запуск через Docker и Docker Compose для удобства локальной разработки и тестирования.
```

Нужно создать .env файл в корне проекта
Пример:
```
DB_HOST=localhost
DB_PORT=5432
DB_USER=hero
DB_PASS=hero
DB_NAME=heroes

TOKEN_HERO=... можно получать через сайт https://superheroapi.com/

TEST_DB_HOST=localhost
TEST_DB_PORT=5433
TEST_DB_USER=test_hero
TEST_DB_PASS=test_hero
TEST_DB_NAME=test_heroes
```

Для запуска через докер:  
Скачиваем образы и запускаем контейнеры.  
Скопирует локальный проект в контейнер и установить все зависимости
```
docker compose up -d
```
Выполняем миграции
```
docker compose exec web alembic upgrade head
```
Для запуска тестов
```
docker compose exec web pytest
```

Документация будет доступна по ссылке
```
http://localhost:8000/docs
```
  
  
Автор — Никита Ефремов  
телеграм @vomerf
