"""
Restaurants Router — Browse restaurants and menus
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database.connection import get_db
from database.models import Restaurant, MenuItem
from api.schemas.schemas import RestaurantWithMenuOut, MenuItemOut

router = APIRouter(prefix="/api/restaurants", tags=["Restaurants"])


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    """Get list of popular cuisine categories."""
    cuisines = db.query(Restaurant.cuisine_type).distinct().filter(Restaurant.is_active == True).all()
    categories = sorted(list({c[0] for c in cuisines if c[0]}))
    return categories


@router.get("/", response_model=List[RestaurantWithMenuOut])
def list_restaurants(
    cuisine: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List all active restaurants with their signature menu dishes."""
    query = db.query(Restaurant).filter(Restaurant.is_active == True)

    if cuisine and cuisine.lower() != "all":
        query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Restaurant.name.ilike(search_filter)) |
            (Restaurant.cuisine_type.ilike(search_filter)) |
            (Restaurant.address.ilike(search_filter))
        )

    return query.order_by(Restaurant.rating.desc()).offset(offset).limit(limit).all()


@router.get("/{restaurant_id}", response_model=RestaurantWithMenuOut)
def get_restaurant(
    restaurant_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific restaurant by ID with its menu."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@router.get("/{restaurant_id}/menu", response_model=List[MenuItemOut])
def get_restaurant_menu(
    restaurant_id: str,
    db: Session = Depends(get_db),
):
    """Get all dishes for a specific restaurant."""
    items = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id).all()
    return items

