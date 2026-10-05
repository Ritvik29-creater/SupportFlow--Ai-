"""
Database Models — SQLAlchemy ORM
Tables: customers, restaurants, orders, order_items, payments, refunds, support_tickets
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, ForeignKey,
    Enum, Text, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


# ─── Enums ────────────────────────────────────────────────────────────────────

class OrderStatus(str, enum.Enum):
    placed = "placed"
    confirmed = "confirmed"
    preparing = "preparing"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    cancelled = "cancelled"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"


class RefundStatus(str, enum.Enum):
    requested = "requested"
    under_review = "under_review"
    approved = "approved"
    rejected = "rejected"
    processed = "processed"


class TicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class TicketCategory(str, enum.Enum):
    order_tracking = "order_tracking"
    payment = "payment"
    refund = "refund"
    restaurant = "restaurant"
    general_support = "general_support"
    unknown = "unknown"


class UserRole(str, enum.Enum):
    customer = "customer"
    support_agent = "support_agent"
    admin = "admin"


# ─── Models ───────────────────────────────────────────────────────────────────

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, unique=True, nullable=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.customer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("Order", back_populates="customer")
    support_tickets = relationship("SupportTicket", back_populates="customer")


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    cuisine_type = Column(String)
    address = Column(Text)
    phone = Column(String)
    rating = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    delivery_time_min = Column(Integer, default=30)  # minutes
    min_order_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="restaurant")
    menu_items = relationship("MenuItem", back_populates="restaurant", cascade="all, delete-orphan")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(String, primary_key=True, default=gen_uuid)
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, default="Main Course")
    is_veg = Column(Boolean, default=False)
    rating = Column(Float, default=4.5)
    image_emoji = Column(String, default="🍲")
    created_at = Column(DateTime, default=datetime.utcnow)

    restaurant = relationship("Restaurant", back_populates="menu_items")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=gen_uuid)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.placed)
    delivery_address = Column(Text, nullable=False)
    total_amount = Column(Float, nullable=False)
    delivery_fee = Column(Float, default=0.0)
    estimated_delivery_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    driver_name = Column(String, nullable=True)
    driver_phone = Column(String, nullable=True)
    special_instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="orders")
    restaurant = relationship("Restaurant", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    payment = relationship("Payment", back_populates="order", uselist=False)
    refunds = relationship("Refund", back_populates="order")
    support_tickets = relationship("SupportTicket", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String, primary_key=True, default=gen_uuid)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    customizations = Column(Text, nullable=True)

    order = relationship("Order", back_populates="items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=gen_uuid)
    order_id = Column(String, ForeignKey("orders.id"), unique=True, nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False)  # card, upi, wallet, cod
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    transaction_id = Column(String, unique=True, nullable=True)
    gateway_response = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = relationship("Order", back_populates="payment")


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(String, primary_key=True, default=gen_uuid)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(RefundStatus), default=RefundStatus.requested)
    refund_method = Column(String, nullable=True)  # original, wallet
    admin_notes = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = relationship("Order", back_populates="refunds")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(String, primary_key=True, default=gen_uuid)
    ticket_number = Column(String, unique=True, nullable=False)  # TKT-XXXX
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    order_id = Column(String, ForeignKey("orders.id"), nullable=True)
    category = Column(Enum(TicketCategory), default=TicketCategory.general_support)
    status = Column(Enum(TicketStatus), default=TicketStatus.open)
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    conversation_log = Column(JSON, nullable=True)  # full chat history
    assigned_agent_id = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="support_tickets")
    order = relationship("Order", back_populates="support_tickets")
