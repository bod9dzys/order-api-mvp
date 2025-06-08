from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="client")  # admin / client


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    latitude = Column(Float, nullable=False, default=50.4501)
    longitude = Column(Float, nullable=False, default=30.5234)

    # Зворотній зв’язок: у одного Customer може бути багато Order
    orders = relationship("Order", back_populates="customer")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    sku = Column(String(50), unique=True, nullable=False)
    price = Column(Float, nullable=False, default=0)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default="new")  # new / paid / shipped
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # Зв’язок: кожне замовлення належить одному клієнту
    customer = relationship("Customer", back_populates="orders")
    # Зв’язок: у одного Order може бути багато OrderItem; cascade для видалення “дочірніх” елементів
    items = relationship(
        "OrderItem",
        cascade="all, delete-orphan",
        back_populates="order"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)

    # Зв’язок: кожен елемент замовлення належить одному Order
    order = relationship("Order", back_populates="items")
    # Зв’язок: кожен елемент замовлення пов’язаний з одним Product
    product = relationship("Product")
