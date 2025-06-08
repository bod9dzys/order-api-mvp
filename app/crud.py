from sqlalchemy.orm import Session
from passlib.context import CryptContext
from . import models, schemas
from app.utils.geography import haversine_km
from app.constants import (
    WAREHOUSE_LAT, WAREHOUSE_LON,
    AVG_SPEED_KM_PER_MIN, CO2_PER_KM, MERGE_RADIUS_KM,
)
import base64, json
from sqlalchemy import select

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------- Users ----------
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed = pwd_context.hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ---------- Products ----------
def create_product(db: Session, prod: schemas.ProductCreate):
    db_obj = models.Product(**prod.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_products(db: Session, skip: int = 0, limit: int = 50):
    return db.query(models.Product).offset(skip).limit(limit).all()

# ---------- Customers ----------
def create_customer(db: Session, cust: schemas.CustomerCreate):
    db_obj = models.Customer(**cust.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

# ---------- Orders ----------
def create_order(db: Session, order: schemas.OrderCreate):
    db_order = models.Order(customer_id=order.customer_id)
    db.add(db_order)
    db.flush()                   # отримаємо id

    for it in order.items:
        db.add(models.OrderItem(order_id=db_order.id, **it.dict()))

    db.commit()
    db.refresh(db_order)
    return db_order

def calculate_order_eta(db: Session, order_id: int) -> schemas.OrderETA:
    """
    Обчислює відстань, ETA, CO₂ та потенційне замикання в один рейс.
    """
    order = (
        db.query(models.Order)
          .options(joinedload(models.Order.customer))
          .filter(models.Order.id == order_id)
          .one()
    )

    cust = order.customer
    distance = haversine_km(
        WAREHOUSE_LAT, WAREHOUSE_LON,
        cust.latitude, cust.longitude
    )
    eta = int(distance / AVG_SPEED_KM_PER_MIN)
    co2 = round(distance * CO2_PER_KM, 2)

    merge_id: int | None = None
    open_orders = (
        db.query(models.Order)
          .join(models.Customer)
          .filter(models.Order.status == "pending",
                  models.Order.id != order.id)
    )
    for other in open_orders:
        d = haversine_km(
            cust.latitude, cust.longitude,
            other.customer.latitude, other.customer.longitude
        )
        if d < MERGE_RADIUS_KM:
            merge_id = other.id
            break

    return schemas.OrderETA(
        order_id=order.id,
        distance_km=round(distance, 2),
        eta_minutes=eta,
        co2_grams=co2,
        suggested_merge_with=merge_id,
    )

def _encode_cursor(order):
    payload = {"id": order.id}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()

def _decode_cursor(cursor: str):
    try:
        obj = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        return obj.get("id")
    except Exception:
        return None

def get_orders_cursor(db: Session, limit: int, cursor: str | None):
    stmt = select(models.Order).order_by(models.Order.id.asc())
    if cursor:
        last_id = _decode_cursor(cursor)
        if last_id:
            stmt = stmt.where(models.Order.id > last_id)

    items = db.scalars(stmt.limit(limit + 1)).all()

    next_cursor = None
    if len(items) > limit:
        last = items.pop()
        next_cursor = _encode_cursor(last)

    return items, next_cursor
