import os
import pytest
from datetime import datetime, timedelta
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from jose import jwt

from app.main import app
from app import models
from app.database import Base
from app.dependencies import get_current_user, get_db

# базові налаштування JWT (хоч і не потрібні після override)
SECRET_KEY = os.getenv("SECRET_KEY", "change_me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "5"))


@pytest.mark.asyncio
async def test_order_eta(tmp_db: Session):
    # ── Ensure тестова БД має таблиці ───────────────────────
    Base.metadata.create_all(bind=tmp_db.bind)

    # ── Arrange ────────────────────────────────────────────
    # 1) Тестовий користувач
    test_user = models.User(
        email="user_eta@example.com",
        hashed_password="not_real_password",
        role="client",
    )
    tmp_db.add(test_user)
    tmp_db.commit()

    # 2) Override залежностей FastAPI → використовуємо tmp_db
    async def _override_user():
        return test_user

    def _override_db() -> AsyncGenerator[Session, None]:
        try:
            yield tmp_db
        finally:
            pass

    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db

    # 3) Створюємо Customer / Product / Order / OrderItem
    customer = models.Customer(
        full_name="Test Customer",
        email="cust_eta@example.com",
        latitude=50.4501,   # ← правильно
        longitude=30.5234,  # ← правильно
    )

    product = models.Product(
        name="Test Product",
        sku="TEST-ETA-001",
        price=15.0,
    )
    order = models.Order(customer=customer, status="pending")
    item = models.OrderItem(order=order, product=product, quantity=3)

    tmp_db.add_all([customer, product, order, item])
    tmp_db.commit()

    # ── Act ────────────────────────────────────────────────
    url = f"/api/v1/orders/{order.id}/eta"
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.get(url)

    # ── Assert ─────────────────────────────────────────────
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == order.id
    assert data["distance_km"] == 0.0
    assert data["eta_minutes"] == 0.0
    assert data["co2_grams"] == 0.0

    # ── Cleanup overrides ─────────────────────────────────
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)
