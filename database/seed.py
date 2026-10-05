"""
Database Seed Script for SupportFlow AI
Populates PostgreSQL with realistic food delivery demo data:
- Customers (demo user & admin)
- Restaurants
- Orders with various statuses (placed, preparing, out_for_delivery, delivered)
- Order items
- Payments
- Sample refund requests
"""
import uuid
from datetime import datetime, timedelta
from database.connection import engine, SessionLocal, create_tables
from database.models import (
    Base, Customer, Restaurant, Order, OrderItem, Payment, Refund, SupportTicket,
    OrderStatus, PaymentStatus, RefundStatus, TicketStatus, TicketCategory, UserRole
)
from api.auth.jwt_handler import hash_password


def seed_database():
    print("🌱 Initializing database schema...")
    create_tables()
    db = SessionLocal()

    # Check if already seeded
    if db.query(Customer).first():
        print("ℹ️ Database already contains records. Skipping seed.")
        db.close()
        return

    print("🚀 Seeding demo data...")

    # 1. Customers
    customer_1 = Customer(
        id=str(uuid.uuid4()),
        email="customer@example.com",
        phone="+1234567890",
        full_name="Alex Johnson",
        hashed_password=hash_password("password123"),
        role=UserRole.customer,
        is_active=True,
    )
    admin_user = Customer(
        id=str(uuid.uuid4()),
        email="admin@supportflow.ai",
        phone="+1987654321",
        full_name="Support Operations Lead",
        hashed_password=hash_password("admin123"),
        role=UserRole.admin,
        is_active=True,
    )
    db.add_all([customer_1, admin_user])
    db.commit()

    # 2. Restaurants
    rest_1 = Restaurant(
        id=str(uuid.uuid4()),
        name="Artisan Burger Co.",
        cuisine_type="American / Burgers",
        address="742 Evergreen Terrace, Sector 4",
        phone="+1555234567",
        rating=4.7,
        is_active=True,
        delivery_time_min=25,
        min_order_amount=15.0,
    )
    rest_2 = Restaurant(
        id=str(uuid.uuid4()),
        name="Napoli Woodfired Pizza",
        cuisine_type="Italian / Pizza",
        address="120 Baker Street, Downtown",
        phone="+1555987654",
        rating=4.9,
        is_active=True,
        delivery_time_min=35,
        min_order_amount=20.0,
    )
    rest_3 = Restaurant(
        id=str(uuid.uuid4()),
        name="Tokyo Ramen & Bowls",
        cuisine_type="Japanese / Asian",
        address="88 Sakura Lane, Midtown",
        phone="+1555333444",
        rating=4.8,
        is_active=True,
        delivery_time_min=30,
        min_order_amount=18.0,
    )
    db.add_all([rest_1, rest_2, rest_3])
    db.commit()

    # 3. Active Order (Out for delivery)
    order_active = Order(
        id="ORD-90210",
        customer_id=customer_1.id,
        restaurant_id=rest_1.id,
        status=OrderStatus.out_for_delivery,
        delivery_address="456 Maple St, Apt 3B, Metropolis",
        total_amount=32.50,
        delivery_fee=3.99,
        estimated_delivery_at=datetime.utcnow() + timedelta(minutes=12),
        driver_name="Michael Rodriguez",
        driver_phone="+1555777888",
        special_instructions="Ring doorbell and leave at door.",
        created_at=datetime.utcnow() - timedelta(minutes=25),
    )
    db.add(order_active)
    db.commit()

    # Items for active order
    item_1 = OrderItem(
        id=str(uuid.uuid4()),
        order_id=order_active.id,
        item_name="Double Truffle Smash Burger",
        quantity=2,
        unit_price=12.50,
        total_price=25.00,
        customizations="No pickles, extra cheese",
    )
    item_2 = OrderItem(
        id=str(uuid.uuid4()),
        order_id=order_active.id,
        item_name="Seasoned Waffle Fries",
        quantity=1,
        unit_price=3.51,
        total_price=3.51,
        customizations="Extra spicy seasoning",
    )
    payment_active = Payment(
        id=str(uuid.uuid4()),
        order_id=order_active.id,
        customer_id=customer_1.id,
        amount=32.50,
        payment_method="card",
        status=PaymentStatus.completed,
        transaction_id="TXN_987654321",
    )
    db.add_all([item_1, item_2, payment_active])

    # 4. Past Delivered Order (eligible for refund demo)
    order_past = Order(
        id="ORD-84512",
        customer_id=customer_1.id,
        restaurant_id=rest_2.id,
        status=OrderStatus.delivered,
        delivery_address="456 Maple St, Apt 3B, Metropolis",
        total_amount=28.00,
        delivery_fee=2.99,
        estimated_delivery_at=datetime.utcnow() - timedelta(hours=3),
        delivered_at=datetime.utcnow() - timedelta(hours=2, minutes=50),
        driver_name="Sarah Chen",
        driver_phone="+1555123987",
        created_at=datetime.utcnow() - timedelta(hours=3, minutes=30),
    )
    db.add(order_past)
    db.commit()

    item_3 = OrderItem(
        id=str(uuid.uuid4()),
        order_id=order_past.id,
        item_name="Margherita D.O.C Pizza",
        quantity=1,
        unit_price=18.00,
        total_price=18.00,
        customizations="Crispy crust",
    )
    item_4 = OrderItem(
        id=str(uuid.uuid4()),
        order_id=order_past.id,
        item_name="Tiramisu Classico",
        quantity=1,
        unit_price=7.01,
        total_price=7.01,
    )
    payment_past = Payment(
        id=str(uuid.uuid4()),
        order_id=order_past.id,
        customer_id=customer_1.id,
        amount=28.00,
        payment_method="upi",
        status=PaymentStatus.completed,
        transaction_id="TXN_1122334455",
    )
    db.add_all([item_3, item_4, payment_past])

    # 5. Sample Support Ticket
    ticket_demo = SupportTicket(
        id=str(uuid.uuid4()),
        ticket_number="TKT-DEMO101",
        customer_id=customer_1.id,
        order_id=order_past.id,
        category=TicketCategory.refund,
        status=TicketStatus.resolved,
        subject="Item missing from order",
        description="Dessert tiramisu was missing from the package.",
    )
    db.add(ticket_demo)
    db.commit()

    db.close()
    print("✅ Seed completed successfully! Demo user: customer@example.com / password123")


if __name__ == "__main__":
    seed_database()
