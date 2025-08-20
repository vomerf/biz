# Install Biz (FastAPI Authorization Service)

🚀 Сервис авторизации на FastAPI с JWT, PostgreSQL и Docker.

## Стек технологий
- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy (async)
- Alembic
- Docker / Docker Compose
- JWT авторизация

---

## Установка и запуск

### 1. Клонируем репозиторий
```bash
git clone <your-repo-url>
cd biz

Создаем .env файл в корне проекта
DB_HOST=db
DB_PORT=5432
DB_USER=biz
DB_PASS=biz
DB_NAME=biz
SECRET_KEY=можно написать любое значение

docker-compose up --build -d
docker-compose exec web alembic upgrade head
```


Сервис будет доступен по адресу: http://localhost:8000

Swagger UI: http://localhost:8000/docs
