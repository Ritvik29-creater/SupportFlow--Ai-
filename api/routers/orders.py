"""
Orders Router — Get orders, order details, order status
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database.connection import get_db
from database.models import Order, Customer
from api.schemas.schemas import OrderOut
from api.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.get("/", response_model=List[OrderOut])
def get_my_orders(
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    """Get all orders for the current customer."""
    orders = (
        db.query(Order)
        .filter(Order.customer_id == current_user.id)
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return orders


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: str,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific order by ID (must belong to current user)."""
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.customer_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order


@router.get("/{order_id}/tracking")
def get_order_tracking(
    order_id: str,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get real-time tracking info for an active order."""
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.customer_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "order_id": order.id,
        "status": order.status,
        "estimated_delivery_at": order.estimated_delivery_at,
        "driver_name": order.driver_name,
        "restaurant_name": order.restaurant.name if order.restaurant else None,
    }
