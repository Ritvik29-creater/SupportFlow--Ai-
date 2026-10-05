"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    full_name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str


# ─── Customer Schemas ─────────────────────────────────────────────────────────

class CustomerOut(BaseModel):
    id: str
    email: str
    phone: Optional[str]
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Restaurant Schemas ───────────────────────────────────────────────────────

class RestaurantOut(BaseModel):
    id: str
    name: str
    cuisine_type: Optional[str]
    address: Optional[str]
    rating: float
    is_active: bool
    delivery_time_min: int
    min_order_amount: float

    class Config:
        from_attributes = True


class MenuItemOut(BaseModel):
    id: str
    restaurant_id: str
    name: str
    price: float
    description: Optional[str] = None
    category: Optional[str] = None
    is_veg: bool = False
    rating: float = 4.5
    image_emoji: str = "🍲"

    class Config:
        from_attributes = True


class RestaurantWithMenuOut(RestaurantOut):
    menu_items: List[MenuItemOut] = []


# ─── Order Schemas ────────────────────────────────────────────────────────────

class OrderItemOut(BaseModel):
    id: str
    item_name: str
    quantity: int
    unit_price: float
    total_price: float
    customizations: Optional[str]

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: str
    customer_id: str
    restaurant_id: str
    status: str
    delivery_address: str
    total_amount: float
    delivery_fee: float
    estimated_delivery_at: Optional[datetime]
    delivered_at: Optional[datetime]
    driver_name: Optional[str]
    special_instructions: Optional[str]
    created_at: datetime
    items: List[OrderItemOut] = []

    class Config:
        from_attributes = True


# ─── Payment Schemas ──────────────────────────────────────────────────────────

class PaymentOut(BaseModel):
    id: str
    order_id: str
    amount: float
    payment_method: str
    status: str
    transaction_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Refund Schemas ───────────────────────────────────────────────────────────

class RefundRequest(BaseModel):
    order_id: str
    amount: float
    reason: str
    refund_method: Optional[str] = "original"  # "original" or "wallet"


class RefundOut(BaseModel):
    id: str
    order_id: str
    amount: float
    reason: str
    status: str
    refund_method: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Support Ticket Schemas ───────────────────────────────────────────────────

class TicketOut(BaseModel):
    id: str
    ticket_number: str
    customer_id: str
    order_id: Optional[str]
    category: str
    status: str
    subject: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Chat Schemas ─────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    content: str
    session_id: Optional[str] = None
    order_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    action: str  # "answer" | "clarify" | "escalate"
    intent: str
    confidence: Optional[float] = None
    ticket_id: Optional[str] = None
    session_id: str
    sentiment: Optional[str] = None          # Customer emotional state
    sentiment_urgency: Optional[str] = None  # low | medium | high
    agent_used: Optional[str] = None         # Which specialized agent handled it


# ─── HITL (Human-in-the-Loop) Schemas ────────────────────────────────────────

class HITLTicketOut(BaseModel):
    ticket_id: str
    session_id: Optional[str]
    intent: str
    priority: str
    sentiment: str
    urgency: str
    user_query: str
    status: str
    created_at: str
    human_response: Optional[str] = None


class HITLUpdateRequest(BaseModel):
    status: str  # "in_review" | "resolved" | "closed"
    human_response: Optional[str] = None
    agent_id: Optional[str] = "human_agent"


class FeedbackRequest(BaseModel):
    session_id: str
    rating: int  # 1-5 stars
    helpful: bool
    comment: Optional[str] = None
