# app/main.py
from fastapi import FastAPI
from .routers import health, auth, products, customers, orders

app = FastAPI(
    title="Order API MVP",
    version="1.0.0"
)

API_PREFIX = "/api/v1"  # ← єдина точка зміни версії

# однаковий префікс під час підключення всіх роутерів
app.include_router(health.router,    prefix=API_PREFIX)
app.include_router(auth.router,      prefix=API_PREFIX)
app.include_router(products.router,  prefix=API_PREFIX)
app.include_router(customers.router, prefix=API_PREFIX)
app.include_router(orders.router,    prefix=API_PREFIX)
