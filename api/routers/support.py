"""
Support Tickets Router — Create, list, and get support tickets
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from database.connection import get_db
from database.models import SupportTicket, Customer, TicketCategory, TicketStatus
from api.schemas.schemas import TicketOut
from api.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/support", tags=["Support Tickets"])


def generate_ticket_number() -> str:
    return f"TKT-{uuid.uuid4().hex[:8].upper()}"


@router.get("/tickets/", response_model=List[TicketOut])
def list_my_tickets(
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all support tickets for the current customer."""
    tickets = (
        db.query(SupportTicket)
        .filter(SupportTicket.customer_id == current_user.id)
        .order_by(SupportTicket.created_at.desc())
        .all()
    )
    return tickets


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: str,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific support ticket."""
    ticket = (
        db.query(SupportTicket)
        .filter(
            SupportTicket.id == ticket_id,
            SupportTicket.customer_id == current_user.id,
        )
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("/tickets/", response_model=TicketOut, status_code=201)
def create_ticket(
    subject: str,
    description: str,
    category: str = "general_support",
    order_id: str = None,
    current_user: Customer = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually create a support ticket."""
    ticket = SupportTicket(
        id=str(uuid.uuid4()),
        ticket_number=generate_ticket_number(),
        customer_id=current_user.id,
        order_id=order_id,
        category=TicketCategory(category) if category in TicketCategory.__members__ else TicketCategory.general_support,
        status=TicketStatus.open,
        subject=subject,
        description=description,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket
