from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime
from typing import List, Optional, Generic, TypeVar

# ---------- Users ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4)

class UserRead(BaseModel):
    id: int
    email: EmailStr
    role: str
    model_config = ConfigDict(from_attributes=True)

# ---------- Customers ----------
class CustomerBase(BaseModel):
    full_name: str
    email: EmailStr
    lat: float
    lon: float

class CustomerCreate(CustomerBase):
    pass

class CustomerRead(CustomerBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class CustomerUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

# ---------- Products ----------
class ProductBase(BaseModel):
    name: str
    sku: str
    price: float

class ProductCreate(ProductBase):
    pass

class ProductRead(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

# ---------- Orders ----------
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = 1

class OrderItemRead(OrderItemCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class OrderCreate(BaseModel):
    customer_id: int
    items: List[OrderItemCreate]

class OrderRead(BaseModel):
    id: int
    created_at: datetime
    status: str
    customer: CustomerRead
    items: List[OrderItemRead]
    model_config = ConfigDict(from_attributes=True)

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class OrderETA(BaseModel):
    order_id: int
    distance_km: float
    eta_minutes: float
    co2_grams: float
    suggested_merge_with: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

# ---------- Errors ----------
class ErrorSchema(BaseModel):
    detail: str

T = TypeVar("T")

class CursorPage(BaseModel, Generic[T]):
    data: List[T]
    next_cursor: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
