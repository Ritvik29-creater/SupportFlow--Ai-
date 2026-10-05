"""
Payments Router — View payment history and payment details
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.connection import get_db
from database.models import Payment, Customer
from api.schemas.schemas import PaymentOut
from api.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/payments", tags=["Payments"])


@router.get("/", response_model=List[PaymentOut])
def get_my_payments(
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20,
):
    """Get payment history for the current customer."""
    payments = (
        db.query(Payment)
        .filter(Payment.customer_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .limit(limit)
        .all()
    )
    return payments


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(
    payment_id: str,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific payment record."""
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id, Payment.customer_id == current_user.id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment
