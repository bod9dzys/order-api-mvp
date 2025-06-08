import os
import pytest
from datetime import datetime, timedelta

from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from jose import jwt

from app.main import app
from app import models

# Параметри, які ваш API використовує для генерації JWT
SECRET_KEY = os.getenv("SECRET_KEY", "change_me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "5"))


@pytest.mark.asyncio
async def test_order_eta(tmp_db: Session):
    # ── Arrange ───────────────────────────────────────────
    # 1) Створюємо в tmp_db «тестового» User
    test_user = models.User(
        email="user_eta@example.com",
        hashed_password="not_real_password",  # не оброблятиме пароль у цьому тесті
        role="client"
    )
    tmp_db.add(test_user)
    tmp_db.commit()

    # 2) Генеруємо JWT для цього користувача
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": test_user.email,
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    headers = {"Authorization": f"Bearer {token}"}

    # 3) Створюємо Customer / Product / Order / OrderItem
    customer = models.Customer(
        full_name="Test Customer",
        email="cust_eta@example.com",
        latitude=50.4501,
        longitude=30.5234,
    )
    product = models.Product(
        name="Test Product",
        sku="TEST-ETA-001",
        price=15.0
    )
    order = models.Order(
        customer=customer,
        status="pending"
    )
    item = models.OrderItem(
        order=order,
        product=product,
        quantity=3
    )

    tmp_db.add_all([customer, product, order, item])
    tmp_db.commit()

    url = f"/orders/{order.id}/eta"

    # ── Act ──────────────────────────────────────────────
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=headers,
    ) as ac:
        response = await ac.get(url)

    # ── Assert ────────────────────────────────────────────
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == order.id
    assert isinstance(data["distance_km"], float)
    assert isinstance(data["eta_minutes"], float)
    assert isinstance(data["co2_grams"], float)

    # Оскільки координати клієнта і складу співпадають, всі ці значення мають бути нульовими
    assert data["distance_km"] == 0.0
    assert data["eta_minutes"] == 0.0
    assert data["co2_grams"] == 0.0
    assert data["suggested_merge_with"] is None
