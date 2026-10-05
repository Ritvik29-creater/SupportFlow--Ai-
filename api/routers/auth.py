"""
Auth Router — Register, Login, Me
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Customer
from api.schemas.schemas import RegisterRequest, LoginRequest, TokenResponse, CustomerOut
from api.auth.jwt_handler import hash_password, verify_password, create_access_token
from api.auth.dependencies import get_current_user
import uuid

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new customer account."""
    existing = db.query(Customer).filter(Customer.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    customer = Customer(
        id=str(uuid.uuid4()),
        email=payload.email,
        phone=payload.phone,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    token = create_access_token({"sub": customer.id, "role": customer.role})
    return TokenResponse(
        access_token=token,
        user_id=customer.id,
        email=customer.email,
        role=customer.role,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Login and receive JWT access token."""
    customer = db.query(Customer).filter(Customer.email == payload.email).first()
    if not customer or not verify_password(payload.password, customer.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": customer.id, "role": customer.role})
    return TokenResponse(
        access_token=token,
        user_id=customer.id,
        email=customer.email,
        role=customer.role,
    )


@router.get("/me", response_model=CustomerOut)
def get_me(current_user: Customer = Depends(get_current_user)):
    """Get current authenticated user's profile."""
    return current_user
