# app/database.py

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# 1. Зчитуємо DATABASE_URL з оточення (Docker-compose, .env або те, що ви вказали)
#    Якщо DATABASE_URL прописано у docker-compose.yml як
#    "postgresql://postgres:postgres@db:5432/order_db",
#    SQLAlchemy працюватиме саме з цим рядком.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/order_db"
)

# 2. Створюємо SQLAlchemy Engine
#    Параметр future=True дає нам сумісність із 2.0-стилем SQLAlchemy.
engine = create_engine(
    DATABASE_URL,
    echo=False,       # echo=True покаже у логи всі SQL-запити (для дебагу)
    future=True
)

# 3. Створюємо SessionLocal — «фабрику» для отримання сесії
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)

# 4. Базовий клас для ORM-моделей
Base = declarative_base()


# 5. Тепер саме та функція, яку імпортує dependencies.py під назвою get_db:
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI залежність для отримання SQLAlchemy Session.
    Використовується як Depends(get_db) у роутерах.

    При кожному виклику get_db() робиться нове з'єднання з БД,
    yield повертає сесію, а після завершення запиту (або при
    виключенні) автоматично закриває її.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
