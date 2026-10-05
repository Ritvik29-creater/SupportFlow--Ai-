"""
Restaurants Router — Browse restaurants
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database.connection import get_db
from database.models import Restaurant, Customer
from api.schemas.schemas import RestaurantOut
from api.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/restaurants", tags=["Restaurants"])


@router.get("/", response_model=List[RestaurantOut])
def list_restaurants(
    cuisine: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """List all active restaurants, with optional cuisine and name filters."""
    query = db.query(Restaurant).filter(Restaurant.is_active == True)

    if cuisine:
        query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))
    if search:
        query = query.filter(Restaurant.name.ilike(f"%{search}%"))

    return query.order_by(Restaurant.rating.desc()).all()


@router.get("/{restaurant_id}", response_model=RestaurantOut)
def get_restaurant(
    restaurant_id: str,
    db: Session = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Get a specific restaurant by ID."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant
