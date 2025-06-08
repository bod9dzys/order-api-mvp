import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from httpx import AsyncClient
from fastapi import status

@pytest.fixture(scope="function")
def tmp_db():
    """
    Створюємо in-memory SQLite-базу і замінюємо залежність get_db у FastAPI
    на нашу тестову сесію. Повертаємо саму сесію для безпосередньої роботи.
    """
    # 1. Налаштовуємо “in-memory” SQLite
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    # 2. Створюємо всі таблиці
    Base.metadata.create_all(bind=engine)

    # 3. Готовий генератор, який FastAPI використовуватиме замість реального get_db()
    def _get_test_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # 4. Перевизначаємо залежність у самому об’єкті app
    app.dependency_overrides[get_db] = _get_test_db

    # 5. Повертаємо тестову сесію (щоб у тестах можна було напряму додавати/чекати дані)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Після тесту повертаємо поведінку get_db до дефолтної (щоб не “затікало” в інші тести)
        app.dependency_overrides.pop(get_db, None)

@pytest.fixture(scope="function")
async def auth_headers(tmp_db):
    """
    Через FastAPI-AsyncClient реєструємо користувача і логінимося,
    щоб отримати JWT для наступних запитів.
    Повертаємо словник із ключем "Authorization": "Bearer <token>".
    """
    test_email = "test_auth@example.com"
    test_password = "TestPass123"

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1) Реєструємо нового користувача
        register_response = await ac.post(
            "/auth/register",
            json={"email": test_email, "password": test_password}
        )
        assert register_response.status_code == status.HTTP_200_OK

        # 2) Авторизуємося (отримуємо JWT)
        login_response = await ac.post(
            "/auth/login",
            data={"username": test_email, "password": test_password},
        )
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json().get("access_token")
        assert token is not None

    return {"Authorization": f"Bearer {token}"}

