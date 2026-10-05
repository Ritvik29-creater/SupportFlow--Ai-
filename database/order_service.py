"""
Order Service — Real Database Integration for SupportFlow Agents
Allows agents to query orders, check live delivery statuses, find customer orders,
and process real refunds in the SQLite database.
"""
import re
from typing import Optional, List, Dict, Any
from database.connection import SessionLocal
from database.models import Order, Restaurant, OrderItem, Payment, Refund, RefundStatus, OrderStatus

def find_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    """Look up an order by ID (case-insensitive, strips '#' or 'ORD-')."""
    if not order_id:
        return None
    
    clean_id = order_id.strip().upper()
    if not clean_id.startswith("ORD-") and clean_id.isdigit():
        clean_id = f"ORD-{clean_id}"

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id.ilike(f"%{clean_id.replace('#', '')}%")).first()
        if not order:
            # Try searching numeric suffix
            digits = re.search(r'\d+', clean_id)
            if digits:
                order = db.query(Order).filter(Order.id.ilike(f"%{digits.group(0)}%")).first()
        
        if not order:
            return None
        
        restaurant = db.query(Restaurant).filter(Restaurant.id == order.restaurant_id).first()
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        payment = db.query(Payment).filter(Payment.order_id == order.id).first()
        refunds = db.query(Refund).filter(Refund.order_id == order.id).all()

        return {
            "order_id": order.id,
            "status": order.status.value if hasattr(order.status, "value") else str(order.status),
            "restaurant_name": restaurant.name if restaurant else "Partner Restaurant",
            "cuisine": restaurant.cuisine_type if restaurant else "",
            "total_amount": f"₹{order.total_amount:.2f}",
            "amount_raw": order.total_amount,
            "delivery_address": order.delivery_address,
            "driver_name": order.driver_name or "Assigned Delivery Partner",
            "driver_phone": order.driver_phone or "+91 98765 43210",
            "estimated_delivery_at": str(order.estimated_delivery_at) if order.estimated_delivery_at else "Within 15 mins",
            "delivered_at": str(order.delivered_at) if order.delivered_at else None,
            "special_instructions": order.special_instructions or "None",
            "items": [
                {
                    "name": item.item_name,
                    "qty": item.quantity,
                    "price": f"₹{item.total_price:.2f}",
                    "customizations": item.customizations or ""
                }
                for item in items
            ],
            "payment_method": payment.payment_method if payment else "UPI",
            "payment_status": payment.status.value if payment and hasattr(payment.status, "value") else "completed",
            "refund_count": len(refunds),
        }
    except Exception as e:
        print(f"[Order Service Error] {e}")
        return None
    finally:
        db.close()


def get_recent_orders(limit: int = 3) -> List[Dict[str, Any]]:
    """Get the most recent orders for context when user hasn't specified an order ID."""
    db = SessionLocal()
    try:
        orders = db.query(Order).order_by(Order.created_at.desc()).limit(limit).all()
        results = []
        for o in orders:
            rest = db.query(Restaurant).filter(Restaurant.id == o.restaurant_id).first()
            items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
            results.append({
                "order_id": o.id,
                "status": o.status.value if hasattr(o.status, "value") else str(o.status),
                "restaurant_name": rest.name if rest else "Restaurant",
                "total_amount": f"₹{o.total_amount:.2f}",
                "driver_name": o.driver_name,
                "items_summary": ", ".join(f"{it.quantity}x {it.item_name}" for it in items[:2]),
            })
        return results
    except Exception as e:
        print(f"[Order Service Recent Error] {e}")
        return []
    finally:
        db.close()


def process_instant_refund(
    order_id: str,
    reason: str,
    method: str = "wallet",
    amount: Optional[float] = None,
    voucher_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a refund or voucher entry in the database for an order with exact amount."""
    db = SessionLocal()
    try:
        clean_id = order_id.strip().upper().replace("#", "")
        order = db.query(Order).filter(Order.id == clean_id).first()
        if not order:
            order = db.query(Order).filter(Order.id.ilike(f"%{clean_id}%")).first()
        if not order:
            return {"success": False, "message": "Order not found"}
        
        # Calculate refund amount (custom partial or full)
        final_amount = amount if amount is not None and amount > 0 else order.total_amount
        # Cap at order total
        if final_amount > order.total_amount:
            final_amount = order.total_amount

        admin_note = f"Processed by SupportFlow AI ({method}): {reason}"
        if voucher_code:
            admin_note += f" | Voucher Issued: {voucher_code}"

        refund = Refund(
            order_id=order.id,
            customer_id=order.customer_id,
            amount=final_amount,
            reason=reason,
            status=RefundStatus.approved if method in ("wallet", "voucher") else RefundStatus.requested,
            refund_method=method,
            admin_notes=admin_note
        )
        db.add(refund)
        db.commit()
        return {
            "success": True,
            "refund_id": refund.id,
            "amount": f"₹{final_amount:.2f}",
            "amount_raw": final_amount,
            "method": method,
            "voucher_code": voucher_code,
            "status": "credited_instantly" if method in ("wallet", "voucher") else "initiated_bank_refund"
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()



def mark_order_as_delivered(order_id: str) -> Optional[Dict[str, Any]]:
    """Mark an order as delivered in SQLite and return full updated order details."""
    db = SessionLocal()
    try:
        clean_id = order_id.replace("#", "").strip().upper()
        order = db.query(Order).filter(Order.id == clean_id).first()
        if not order:
            order = db.query(Order).filter(Order.id.ilike(f"%{clean_id}%")).first()
        if not order:
            return None

        from datetime import datetime
        order.status = OrderStatus.delivered
        order.delivered_at = datetime.utcnow()
        db.commit()

        return find_order_by_id(order.id)
    except Exception as e:
        db.rollback()
        print(f"[Mark Delivered Error] {e}")
        return None
    finally:
        db.close()

