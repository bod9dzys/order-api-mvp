from sqlalchemy.orm import Session
from app import models
from app.utils.geography import haversine_km

# Константи
WAREHOUSE_LAT = 50.4501
WAREHOUSE_LON = 30.5234
AVG_SPEED_KM_PER_MIN = 0.5
CO2_PER_KM_G = 121
MERGE_RADIUS_KM = 3

def calculate_order_eta(order_id: int, db: Session) -> dict:
    """
    Обчислює ETA для замовлення:
    - distance_km: відстань від складу до клієнта (км)
    - eta_minutes: час у хвилинах
    - co2_grams: викиди CO2 (грам)
    - suggested_merge_with: ID іншого pending-замовлення в межах 3 км або None
    """

    # 1. Просто дістаємо замовлення (з клієнтом через join)
    order: models.Order | None = (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .join(models.Customer)
        .first()
    )
    if not order:
        raise ValueError(f"Order {order_id} not found")

    customer = order.customer
    lat_cust = customer.latitude
    lon_cust = customer.longitude

    # 2. Відстань Haversine
    distance = haversine_km(
        WAREHOUSE_LAT, WAREHOUSE_LON,
        lat_cust, lon_cust,
    )
    distance_rounded = round(distance, 2)

    # 3. ETA у хвилинах
    eta = round(distance / AVG_SPEED_KM_PER_MIN, 2)

    # 4. CO2-викиди
    co2 = round(distance * CO2_PER_KM_G, 2)

    # 5. Пошук можливого “злиття” з іншим замовленням:
    pending_orders = (
        db.query(models.Order)
        .filter(
            models.Order.status == "pending",
            models.Order.id != order_id
        )
        .join(models.Customer)
        .order_by(models.Order.created_at)  # найстаріше перше
        .all()
    )

    suggested_id = None
    for other in pending_orders:
        other_lat = other.customer.latitude
        other_lon = other.customer.longitude
        distance_to_other = haversine_km(
            lat_cust, lon_cust,
            other_lat, other_lon,
        )
        if distance_to_other <= MERGE_RADIUS_KM:
            suggested_id = other.id
            break

    return {
        "order_id": order_id,
        "distance_km": distance_rounded,
        "eta_minutes": eta,
        "co2_grams": co2,
        "suggested_merge_with": suggested_id,
    }
