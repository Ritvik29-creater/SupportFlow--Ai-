"""
Orders Router — Get orders, order details, order status, and instant 1-tap ordering
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import random
import uuid

from database.connection import get_db
from database.models import Order, Customer, Restaurant, OrderItem, Payment, OrderStatus, PaymentStatus
from api.schemas.schemas import OrderOut
from api.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/orders", tags=["Orders"])

DRIVERS_POOL = [
    ("Michael Rodriguez", "+1 555 777 888"),
    ("Ramesh Kumar", "+91 98765 12345"),
    ("Suresh Raina", "+91 98111 22334"),
    ("Priya Sharma", "+91 98222 33445"),
    ("Amit Patel", "+91 98333 44556"),
    ("David Miller", "+1 555 234 567"),
]


class QuickOrderInput(BaseModel):
    restaurant_id: str
    dish_name: str
    price: float
    quantity: int = 1
    delivery_address: str = "456 Maple St, Apt 3B, Sector 4"
    special_instructions: Optional[str] = "Ring bell and leave at door"
    payment_method: str = "UPI"


@router.post("/quick-order")
def place_quick_order(
    payload: QuickOrderInput,
    db: Session = Depends(get_db),
):
    """
    1-Tap Quick Order Placement.
    Creates an active order immediately with assigned driver, restaurant link, and live tracking.
    """
    restaurant = db.query(Restaurant).filter(Restaurant.id == payload.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Get or create demo customer
    customer = db.query(Customer).first()
    customer_id = customer.id if customer else "cust_guest_demo"

    # Generate Order ID like ORD-12345
    order_id = f"ORD-{random.randint(10000, 99999)}"
    driver_name, driver_phone = random.choice(DRIVERS_POOL)
    delivery_min = restaurant.delivery_time_min or random.randint(25, 40)
    total_amount = round(payload.price * payload.quantity + 30.0, 2)  # items + ₹30 delivery fee

    order = Order(
        id=order_id,
        customer_id=customer_id,
        restaurant_id=restaurant.id,
        status=OrderStatus.out_for_delivery if random.random() > 0.3 else OrderStatus.preparing,
        delivery_address=payload.delivery_address,
        total_amount=total_amount,
        delivery_fee=30.0,
        estimated_delivery_at=datetime.utcnow() + timedelta(minutes=delivery_min),
        driver_name=driver_name,
        driver_phone=driver_phone,
        special_instructions=payload.special_instructions,
        created_at=datetime.utcnow(),
    )
    db.add(order)
    db.flush()

    # Create Order Item
    item = OrderItem(
        id=f"ITEM-{uuid.uuid4().hex[:8].upper()}",
        order_id=order.id,
        item_name=payload.dish_name,
        quantity=payload.quantity,
        unit_price=payload.price,
        total_price=payload.price * payload.quantity,
        customizations="Fresh & Hot, No plastic cutlery",
    )
    db.add(item)

    # Create Payment Record
    payment = Payment(
        id=f"PAY-{uuid.uuid4().hex[:8].upper()}",
        order_id=order.id,
        customer_id=customer_id,
        amount=total_amount,
        payment_method=payload.payment_method.lower(),
        status=PaymentStatus.completed,
        transaction_id=f"TXN_{uuid.uuid4().hex[:10].upper()}",
    )
    db.add(payment)
    db.commit()

    return {
        "success": True,
        "message": f"Order {order_id} placed successfully!",
        "order": {
            "order_id": order.id,
            "status": order.status.value if hasattr(order.status, "value") else str(order.status),
            "restaurant_name": restaurant.name,
            "dish_name": payload.dish_name,
            "quantity": payload.quantity,
            "total_amount": f"₹{total_amount:.2f}",
            "driver_name": driver_name,
            "driver_phone": driver_phone,
            "delivery_address": order.delivery_address,
            "estimated_delivery_at": order.estimated_delivery_at.strftime("%I:%M %p"),
            "eta_minutes": delivery_min,
        }
    }


@router.get("/list")
def list_all_recent_orders(
    limit: int = 15,
    db: Session = Depends(get_db),
):
    """Get list of active and recent orders with full details for demo tracking."""
    orders = db.query(Order).order_by(Order.created_at.desc()).limit(limit).all()
    results = []
    for o in orders:
        rest = db.query(Restaurant).filter(Restaurant.id == o.restaurant_id).first()
        items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
        results.append({
            "order_id": o.id,
            "status": o.status.value if hasattr(o.status, "value") else str(o.status),
            "restaurant_name": rest.name if rest else "Partner Restaurant",
            "cuisine": rest.cuisine_type if rest else "",
            "total_amount": f"₹{o.total_amount:.2f}",
            "driver_name": o.driver_name or "Assigning partner...",
            "driver_phone": o.driver_phone or "+91 98765 43210",
            "delivery_address": o.delivery_address,
            "estimated_delivery_at": o.estimated_delivery_at.strftime("%I:%M %p") if o.estimated_delivery_at else "30 mins",
            "created_at": o.created_at.strftime("%d %b, %I:%M %p") if o.created_at else "Just now",
            "items": [
                {
                    "name": it.item_name,
                    "qty": it.quantity,
                    "price": f"₹{it.total_price:.2f}"
                }
                for it in items
            ]
        })
    return results


@router.get("/{order_id}/tracking")
def get_order_tracking(
    order_id: str,
    db: Session = Depends(get_db),
):
    """Get real-time tracking info for an active order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    rest = db.query(Restaurant).filter(Restaurant.id == order.restaurant_id).first()
    return {
        "order_id": order.id,
        "status": order.status.value if hasattr(order.status, "value") else str(order.status),
        "estimated_delivery_at": str(order.estimated_delivery_at),
        "driver_name": order.driver_name,
        "driver_phone": order.driver_phone,
        "restaurant_name": rest.name if rest else None,
        "total_amount": f"₹{order.total_amount:.2f}",
    }

