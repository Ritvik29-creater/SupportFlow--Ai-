"""
Refunds Router — Request and track refunds
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime
from database.connection import get_db
from database.models import Refund, Order, Customer, RefundStatus
from api.schemas.schemas import RefundRequest, RefundOut
from api.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/refunds", tags=["Refunds"])


def process_refund_background(refund_id: str):
    """Background task: would notify customer, update payment gateway, etc."""
    # In production: call payment gateway API, send email notification via Redis queue
    pass


@router.post("/", response_model=RefundOut, status_code=201)
def request_refund(
    payload: RefundRequest,
    background_tasks: BackgroundTasks,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a refund request for an order."""
    # Verify order belongs to customer
    order = (
        db.query(Order)
        .filter(Order.id == payload.order_id, Order.customer_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Check if refund already exists for this order
    existing = db.query(Refund).filter(Refund.order_id == payload.order_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A refund request already exists for this order",
        )

    refund = Refund(
        id=str(uuid.uuid4()),
        order_id=payload.order_id,
        customer_id=current_user.id,
        amount=payload.amount,
        reason=payload.reason,
        refund_method=payload.refund_method or "original",
        status=RefundStatus.requested,
    )
    db.add(refund)
    db.commit()
    db.refresh(refund)

    # Queue background processing
    background_tasks.add_task(process_refund_background, refund.id)

    return refund


@router.get("/", response_model=List[RefundOut])
def get_my_refunds(
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all refund requests for the current customer."""
    refunds = (
        db.query(Refund)
        .filter(Refund.customer_id == current_user.id)
        .order_by(Refund.created_at.desc())
        .all()
    )
    return refunds


@router.get("/{refund_id}", response_model=RefundOut)
def get_refund(
    refund_id: str,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific refund request."""
    refund = (
        db.query(Refund)
        .filter(Refund.id == refund_id, Refund.customer_id == current_user.id)
        .first()
    )
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found")
    return refund
