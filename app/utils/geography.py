import math

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Повертає велику окружну відстань між (lat1, lon1) та (lat2, lon2) у кілометрах.
    Радіус Землі = 6 371 км.
    """
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lon2 - lon1)
    a = (math.sin(d_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))
