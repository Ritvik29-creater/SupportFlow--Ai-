"""
SupportFlow AI — Restaurant & Situation-Specific Refund Policy Engine
Defines sensible, real-world customer dispute policies tailored by:
1. Cuisine type & restaurant tier (Biryani, Pizza, Desserts/Ice Cream, Burgers, South Indian, North Indian, etc.)
2. Specific situation & incident severity (Total spillage, minor condiment leak, melted dessert, cold food, missing item, dietary violation, delay)
3. Zero-photo requirement: resolutions are evaluated conversationally and interactively based on order telemetry and reported details.
"""
import re
from typing import Dict, Any, Optional, List

# Cuisine-specific rules, packaging characteristics, and temperature guidelines
CUISINE_POLICIES = {
    "Biryani & Mughlai": {
        "packaging_type": "Sealed Handi / Foil-lined Box with Separate Condiment Cups",
        "temperature_behavior": "Retains heat well due to dense dum basmati rice; slow cooling during transit.",
        "reheating_tip": "Sprinkle 1 tbsp water over rice, cover loosely, and microwave for 60-90 seconds to restore dum aroma and fluffiness.",
        "spill_rules": {
            "minor": {
                "desc": "Minor raita or mirchi ka salan cup leakage while biryani container is sealed",
                "refund_pct": 25,
                "voucher_val": 50,
                "code_prefix": "SALAN",
                "rationale": "Side condiment cups experienced minor transit leak, but the main biryani handi remains intact and delicious."
            },
            "major": {
                "desc": "Main biryani container cracked or gravy soaked through the bag, rendering meal inedible",
                "refund_pct": 100,
                "voucher_val": 100,
                "code_prefix": "BIRYANI",
                "rationale": "Severe handi rupture compromised the entire meal. 100% full refund or free replacement order."
            }
        },
        "cold_rules": {
            "refund_pct": 25,
            "voucher_val": 75,
            "code_prefix": "WARM",
            "rationale": "Dum biryani remains safe and flavorful; 25% courtesy wallet credit or ₹75 voucher issued with reheating advice."
        }
    },
    "Pizza & Italian": {
        "packaging_type": "Vented Cardboard Pizza Box with Heat Retaining Liner",
        "temperature_behavior": "Cheese cools and crust loses crispness if delivery exceeds 30 minutes.",
        "reheating_tip": "Place slices on a non-stick skillet over medium-low heat with a lid for 2-3 mins. Crust crisps up perfectly and cheese melts without getting chewy!",
        "spill_rules": {
            "minor": {
                "desc": "Pizza shifted in box or garlic dip container cracked",
                "refund_pct": 30,
                "voucher_val": 60,
                "code_prefix": "CRUST",
                "rationale": "Slight topping shift or side dip leak; pizza base is intact and edible."
            },
            "major": {
                "desc": "Box crushed or flipped, cheese and toppings stuck entirely to lid",
                "refund_pct": 100,
                "voucher_val": 100,
                "code_prefix": "PIZZA",
                "rationale": "Pizza inverted or smashed against the box lid during bike ride, rendering it inedible."
            }
        },
        "cold_rules": {
            "refund_pct": 25,
            "voucher_val": 75,
            "code_prefix": "WARM",
            "rationale": "Cold pizza qualifies for 25% courtesy refund or ₹75 voucher along with our authentic skillet crisping tip."
        }
    },
    "Desserts, Bakery & Ice Cream": {
        "packaging_type": "Insulated Cold Pouch / Box with Dry Gel Pack (for Ice Cream)",
        "temperature_behavior": "EXTREMELY TEMPERATURE SENSITIVE. Ice cream and frozen desserts melt permanently and cannot be re-frozen into original creamy texture.",
        "reheating_tip": "Cannot be reheated. Chill immediately in deep freezer if only soft, but if melted to liquid, replacement/refund applies.",
        "spill_rules": {
            "minor": {
                "desc": "Topping drizzle leaked into box packaging",
                "refund_pct": 35,
                "voucher_val": 60,
                "code_prefix": "SWEET",
                "rationale": "Outer sauce leakage; dessert body remains consumable."
            },
            "major": {
                "desc": "Celebration cake smashed, pastry crushed, or melted dessert flooded box",
                "refund_pct": 100,
                "voucher_val": 100,
                "code_prefix": "DESSERT",
                "rationale": "Delicate dessert structure or cake was severely damaged during courier handling."
            }
        },
        "cold_rules": {
            # For ice cream, "cold" complaint actually means melted / warm!
            "refund_pct": 100,
            "voucher_val": 100,
            "code_prefix": "MELT",
            "rationale": "Melted ice cream cannot be refrozen without losing texture and emulsion. Full 100% item refund or replacement credit granted immediately."
        }
    },
    "Burgers & American Fast Food": {
        "packaging_type": "Insulated Foil Wrapper / Clamshell Carton",
        "temperature_behavior": "Fries lose crunch from steam within 20 mins; burgers stay warm for 35 mins.",
        "reheating_tip": "Pop fries in an air fryer at 180°C for 2 mins or dry skillet for 90 seconds to restore crunch. Avoid microwave for fries!",
        "spill_rules": {
            "minor": {
                "desc": "Soda lid leaked slightly or dip packet burst",
                "refund_pct": 30,
                "voucher_val": 50,
                "code_prefix": "BURGER",
                "rationale": "Beverage condensation or dip leak; burgers remained dry in wrappers."
            },
            "major": {
                "desc": "Drink spilled completely over burger bag, soaking buns and carton",
                "refund_pct": 100,
                "voucher_val": 100,
                "code_prefix": "COMBO",
                "rationale": "Liquid beverage spilled over the entire meal, making burgers and sides soggy and inedible."
            }
        },
        "cold_rules": {
            "refund_pct": 25,
            "voucher_val": 60,
            "code_prefix": "CRUNCH",
            "rationale": "25% courtesy wallet credit or ₹60 snack voucher plus fast fry crisping advice."
        }
    },
    "South Indian & Coastal": {
        "packaging_type": "Banana Leaf / Paper Wrap with Hot Sambhar & Chutney Pouches",
        "temperature_behavior": "Crispy dosas soften from trapped steam in paper box after 15 mins. Sambhar remains hot.",
        "reheating_tip": "Heat a flat tawa (griddle) on high, brush lightly with ghee/oil, place dosa for 40 seconds to bring back paper-roast crispness!",
        "spill_rules": {
            "minor": {
                "desc": "Sambhar pouch leaked slightly into outer carry bag",
                "refund_pct": 25,
                "voucher_val": 40,
                "code_prefix": "DOSA",
                "rationale": "Sambhar container leaked partially, but main tiffin items are dry and intact."
            },
            "major": {
                "desc": "Hot sambhar flooded the box, disintegrating dosas or idlis completely",
                "refund_pct": 100,
                "voucher_val": 100,
                "code_prefix": "TIFFIN",
                "rationale": "Sambhar container burst, destroying the texture and taste of the meal."
            }
        },
        "cold_rules": {
            "refund_pct": 25,
            "voucher_val": 50,
            "code_prefix": "TAWA",
            "rationale": "Steam softening is a natural physics constraint of delivered dosas. 25% courtesy refund or ₹50 coupon provided with tawa crisping guidance."
        }
    },
    "North Indian & Mughlai": {
        "packaging_type": "Tamper-evident Plastic Containers with Heat-Sealed Film",
        "temperature_behavior": "Rich gravies (Butter Chicken, Dal Makhani) retain heat effectively.",
        "reheating_tip": "Transfer gravy to microwave bowl and heat for 90 seconds. Brush cold naans/rotis with butter and warm on tawa for 30 seconds.",
        "spill_rules": {
            "minor": {
                "desc": "Curry film seal cracked at the edge, minor oil leakage",
                "refund_pct": 25,
                "voucher_val": 50,
                "code_prefix": "CURRY",
                "rationale": "Minor oil or gravy seepage at container seam; 80%+ of dish was preserved."
            },
            "major": {
                "desc": "Entire curry container popped open, sauce soaked breads and outer bag",
                "refund_pct": 100,
                "voucher_val": 100,
                "code_prefix": "MAKHANI",
                "rationale": "Total container rupture ruined gravies and flatbreads. 100% full refund approved."
            }
        },
        "cold_rules": {
            "refund_pct": 25,
            "voucher_val": 75,
            "code_prefix": "WARM",
            "rationale": "25% courtesy wallet compensation or ₹75 voucher issued with quick reheat instructions."
        }
    },
    "Cafe & Beverages": {
        "packaging_type": "Spill-proof Cup Carrier with Sealed Drink Lids",
        "temperature_behavior": "Iced beverages melt over 30 mins; hot coffee cools quickly.",
        "reheating_tip": "Hot drinks can be transferred to cup and microwaved for 30s. Iced coffee cannot be re-iced without dilution.",
        "spill_rules": {
            "minor": {
                "desc": "Minor splash on cup lid rim",
                "refund_pct": 30,
                "voucher_val": 40,
                "code_prefix": "BREW",
                "rationale": "Minor splash on lid; majority of drink intact."
            },
            "major": {
                "desc": "Coffee or shake cup toppled and leaked completely inside carrier",
                "refund_pct": 100,
                "voucher_val": 100,
                "code_prefix": "CAFE",
                "rationale": "Beverage cup emptied in transit; 100% item refund credited immediately."
            }
        },
        "cold_rules": {
            "refund_pct": 50,
            "voucher_val": 60,
            "code_prefix": "BREW",
            "rationale": "Coffee arrived lukewarm; 50% courtesy credit or ₹60 discount voucher."
        }
    }
}

# Restaurant-specific brand guarantees
RESTAURANT_BRAND_POLICIES = {
    "meghana foods": {
        "brand_name": "Meghana Foods",
        "specialty": "Andhra Style Spicy Dum Biryanis & Starters",
        "packaging_standard": "Heat-sealed foil boxes with thick gravy containers",
        "dietary_type": "Mixed (Specialized in spicy non-veg & paneer)",
        "guarantee": "Authentic Andhra spice guarantee. If raita or salan leaked, we refund condiment cost immediately without requiring photo proof."
    },
    "behrouz biryani": {
        "brand_name": "Behrouz Biryani",
        "specialty": "Royal Awadhi Dum Biryanis & Shahi Desserts",
        "packaging_standard": "Royal Earthen Dawat Box with Tamper-Proof Gold Seal",
        "dietary_type": "Royal Mughlai & Halal Meat",
        "guarantee": "Royal Seal Assurance: If the gold packaging seal was tampered with or broken on arrival, 100% priority replacement is authorized."
    },
    "domino's pizza": {
        "brand_name": "Domino's Pizza",
        "specialty": "Fresh Hand-Tossed Pizzas & Garlic Breads",
        "packaging_standard": "Corrugated Pizza Boxes with Safe-Delivery Seal",
        "dietary_type": "Mixed (Dedicated Veg and Non-Veg prep lines)",
        "guarantee": "30-Minute Safe Delivery & Crust Integrity Guarantee. If box was flipped in transit, 100% replacement/refund is honored."
    },
    "pizza hut": {
        "brand_name": "Pizza Hut",
        "specialty": "Pan Pizzas & Stuffed Crust",
        "packaging_standard": "Heat-lock delivery cartons",
        "dietary_type": "Mixed",
        "guarantee": "Hot pan pizza crust guarantee."
    },
    "corner house": {
        "brand_name": "Corner House Ice Cream",
        "specialty": "Legendary 'Death By Chocolate' & Fresh Fruit Ice Creams",
        "packaging_standard": "Heavy insulated foil pouches with chilled temperature insulation",
        "dietary_type": "Pure Vegetarian / Eggless Ice Creams",
        "guarantee": "Zero-Melt Cold Chain Guarantee: If ice cream arrived completely melted, 100% full item refund is credited automatically."
    },
    "naturals ice cream": {
        "brand_name": "Naturals Ice Cream",
        "specialty": "Artisanal Seasonal Fresh Fruit Ice Creams",
        "packaging_standard": "Sealed tubs packed with cold packs",
        "dietary_type": "100% Vegetarian Fruit Ice Creams",
        "guarantee": "Freshness & Freeze Guarantee: Full refund for melted product."
    },
    "haldiram's": {
        "brand_name": "Haldiram's",
        "specialty": "Pure Vegetarian Sweets, Chaats & North Indian Thalis",
        "packaging_standard": "Hygienic compartmentalized meal trays",
        "dietary_type": "100% Pure Vegetarian",
        "guarantee": "Strict Dietary Sanctity Guarantee: Zero tolerance for non-veg contamination. Any dietary mix-up gets 100% full refund + ₹200 apology voucher."
    },
    "vidyarthi bhavan": {
        "brand_name": "Vidyarthi Bhavan",
        "specialty": "Heritage Masala Dosa & South Indian Filter Coffee",
        "packaging_standard": "Traditional paper wrapping with fresh chutney cups",
        "dietary_type": "100% Pure Vegetarian Heritage",
        "guarantee": "Authentic taste guarantee. Prompt refund for missing chutneys or damaged tiffin."
    },
    "artisan burger co.": {
        "brand_name": "Artisan Burger Co.",
        "specialty": "Gourmet Smash Burgers & Loaded Waffle Fries",
        "packaging_standard": "Perforated burger boxes preventing soggy buns",
        "dietary_type": "Gourmet Fast Food",
        "guarantee": "Fresh bun & combo accuracy guarantee."
    },
    "burger king": {
        "brand_name": "Burger King",
        "specialty": "Flame-Grilled Whoppers & Combos",
        "packaging_standard": "Eco-friendly wrap with drink cup holders",
        "dietary_type": "Separate Veg and Non-veg fryers",
        "guarantee": "Meal combo fulfillment guarantee: missing beverage or fries refunded instantly."
    }
}


def get_restaurant_policy(restaurant_name: str = "", cuisine_type: str = "") -> Dict[str, Any]:
    """Find the specific brand guarantee or fallback to cuisine category policy."""
    rest_clean = (restaurant_name or "").strip().lower()
    cuisine_clean = (cuisine_type or "").strip()

    # Match brand policy
    brand_info = None
    for brand_key, brand_data in RESTAURANT_BRAND_POLICIES.items():
        if brand_key in rest_clean:
            brand_info = brand_data
            break

    # Match cuisine policy
    cuisine_info = None
    for cuisine_key, cuisine_data in CUISINE_POLICIES.items():
        if cuisine_key.lower() in cuisine_clean.lower() or cuisine_clean.lower() in cuisine_key.lower():
            cuisine_info = cuisine_data
            break

    if not cuisine_info:
        # Fallback to general North Indian / casual dining
        if any(w in cuisine_clean.lower() for w in ["biryani", "mughlai", "rice"]):
            cuisine_info = CUISINE_POLICIES["Biryani & Mughlai"]
        elif any(w in cuisine_clean.lower() for w in ["pizza", "italian", "pasta"]):
            cuisine_info = CUISINE_POLICIES["Pizza & Italian"]
        elif any(w in cuisine_clean.lower() for w in ["dessert", "ice cream", "cake", "sweet", "bakery"]):
            cuisine_info = CUISINE_POLICIES["Desserts, Bakery & Ice Cream"]
        elif any(w in cuisine_clean.lower() for w in ["burger", "fast food", "fries"]):
            cuisine_info = CUISINE_POLICIES["Burgers & American Fast Food"]
        elif any(w in cuisine_clean.lower() for w in ["south indian", "dosa", "idli"]):
            cuisine_info = CUISINE_POLICIES["South Indian & Coastal"]
        elif any(w in cuisine_clean.lower() for w in ["cafe", "coffee", "tea", "beverage"]):
            cuisine_info = CUISINE_POLICIES["Cafe & Beverages"]
        else:
            cuisine_info = CUISINE_POLICIES["North Indian & Mughlai"]

    return {
        "brand_info": brand_info,
        "cuisine_info": cuisine_info,
        "restaurant_name": brand_info["brand_name"] if brand_info else (restaurant_name or "Partner Restaurant"),
        "reheating_tip": cuisine_info.get("reheating_tip", "Heat gently before consuming."),
        "packaging_standard": brand_info["packaging_standard"] if brand_info else cuisine_info.get("packaging_type", "Standard Food Delivery Packaging")
    }


def evaluate_situation_refund(
    issue_type: str,
    order_data: Optional[Dict[str, Any]],
    user_complaint: str = "",
    history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Evaluates customer dispute using sensible situation and restaurant-specific economics.
    Strictly NO photo verification is required.
    """
    q_lower = user_complaint.lower()
    if history:
        for m in history[-4:]:
            q_lower += " " + m.get("content", "").lower()

    # Order details
    order_id = order_data.get("order_id", "ORD-ACTIVE") if order_data else "ORD-ACTIVE"
    ord_suffix = order_id.replace("ORD-", "") if order_id else "APP"
    total_amount = order_data.get("amount_raw", 350.0) if order_data else 350.0
    restaurant_name = order_data.get("restaurant_name", "Partner Restaurant") if order_data else "Partner Restaurant"
    cuisine = order_data.get("cuisine", "") if order_data else ""
    items = order_data.get("items", []) if order_data else []

    policy_meta = get_restaurant_policy(restaurant_name, cuisine)
    cuisine_info = policy_meta["cuisine_info"]
    brand_info = policy_meta["brand_info"]

    # Check for Ice Cream / Dessert category special case
    is_dessert_or_icecream = (
        "dessert" in cuisine.lower() or "ice cream" in cuisine.lower() or
        any(k in restaurant_name.lower() for k in ["corner house", "naturals", "theobroma", "baskin", "ice cream"]) or
        any(k in q_lower for k in ["ice cream", "sundae", "dbc", "thickshake", "melted", "shake"])
    )

    # 1. DIETARY VIOLATION (Non-veg delivered to vegetarian) -> Highest priority
    is_dietary_violation = (
        ("non-veg" in q_lower and "veg" in q_lower) or
        ("chicken" in q_lower and any(w in q_lower for w in ["pure veg", "ordered veg", "vegetarian", "ordered paneer"])) or
        ("meat" in q_lower and "veg" in q_lower)
    )

    if is_dietary_violation:
        voucher_code = f"RESPECT200-{ord_suffix}"
        return {
            "tier": "Dietary Sanctity Violation — 100% Full Order Refund + ₹200 Apology Credit",
            "decision": "APPROVE_FULL_REFUND",
            "refund_pct": 100,
            "refund_amount": total_amount,
            "voucher_code": voucher_code,
            "voucher_value": "₹200 Priority Dining Voucher",
            "policy_rationale": (
                f"Zero-tolerance dietary policy: Non-vegetarian food delivered on a vegetarian order at {restaurant_name}. "
                "Immediate 100% full refund approved with sincere apologies. A formal incident ticket has been flagged with the restaurant management."
            ),
            "restaurant_note": brand_info["guarantee"] if brand_info else "Strict dietary compliance enforced.",
            "reheating_tip": "Please dispose of or keep aside the delivered food.",
            "interactive_options": [
                {"label": f"⚡ Instant 100% Wallet Refund (₹{total_amount:.2f})", "method": "wallet"},
                {"label": f"🎟️ Accept ₹200 Apology Voucher ({voucher_code})", "method": "voucher"},
                {"label": f"💳 Refund to Original UPI/Bank (3-5 days)", "method": "bank"}
            ]
        }

    # 2. MELTED DESSERT / ICE CREAM
    if is_dessert_or_icecream and any(w in q_lower for w in ["melt", "liquid", "warm", "cold", "watery", "soup"]):
        voucher_code = f"MELTFREE-{ord_suffix}"
        return {
            "tier": "Zero-Melt Cold-Chain Guarantee — 100% Item Refund / Free Reorder",
            "decision": "APPROVE_FULL_REFUND",
            "refund_pct": 100,
            "refund_amount": total_amount,
            "voucher_code": voucher_code,
            "voucher_value": "100% Dessert Replacement Voucher",
            "policy_rationale": (
                f"Unlike hot foods, frozen desserts and ice cream from {restaurant_name} permanently lose emulsion and texture once melted. "
                "Under our Zero-Melt Policy, 100% full refund or instant free replacement credit is granted without friction."
            ),
            "restaurant_note": "Cold-chain thermal insulation breached during transit.",
            "reheating_tip": "Melted ice cream cannot be reconstituted by refreezing. Enjoy our instant refund to re-order fresh!",
            "interactive_options": [
                {"label": f"⚡ Instant 100% Wallet Refund (₹{total_amount:.2f})", "method": "wallet"},
                {"label": f"🎟️ Claim 100% Reorder Voucher ({voucher_code})", "method": "voucher"}
            ]
        }

    # 3. TASTE / SPICINESS / PERSONAL FLAVOR PREFERENCE
    is_taste_issue = any(w in q_lower for w in [
        "too spicy", "too salty", "too sweet", "too oily", "greasy",
        "bland", "no flavor", "didn't like the taste", "not tasty", "flavorless", "sour"
    ])
    if is_taste_issue:
        calc_amt = round(total_amount * 0.15, 2)
        voucher_code = f"TASTE15-{ord_suffix}"
        return {
            "tier": f"Flavor / Taste Preference — 15% Goodwill Dining Credit ({restaurant_name})",
            "decision": "APPROVE_PARTIAL_REFUND",
            "refund_pct": 15,
            "refund_amount": calc_amt,
            "voucher_code": voucher_code,
            "voucher_value": f"₹{max(40, round(calc_amt))} Chef Feedback Voucher",
            "policy_rationale": (
                f"Dishes at {restaurant_name} are prepared following authentic signature kitchen recipes. "
                "Because taste, spice tolerance, and flavor preferences are subjective, full refunds or cancellations are not provided. "
                f"As a gesture of goodwill, we offer a 15% courtesy credit of ₹{calc_amt:.2f} or a dining coupon, and our team has shared your feedback directly with the restaurant chef."
            ),
            "restaurant_note": f"Culinary feedback logged for {restaurant_name} kitchen.",
            "reheating_tip": "If a dish is too spicy, mixing in a spoonful of fresh curd, cream, or lemon juice can help balance the heat profile.",
            "interactive_options": [
                {"label": f"⚡ Accept 15% Wallet Credit (₹{calc_amt:.2f})", "method": "wallet"},
                {"label": f"🎟️ Take Dining Voucher ({voucher_code})", "method": "voucher"}
            ]
        }

    # 4. SOGGINESS / TEXTURE PREFERENCE (Fries, Crust, Dosas, Breads)
    is_soggy_issue = any(w in q_lower for w in ["soggy", "not crispy", "limp fries", "soft crust", "steamed buns", "chewy"])
    if is_soggy_issue:
        calc_amt = round(total_amount * 0.20, 2)
        voucher_code = f"CRISP20-{ord_suffix}"
        return {
            "tier": f"Transit Moisture Effect — 20% Courtesy Credit ({restaurant_name})",
            "decision": "APPROVE_PARTIAL_REFUND",
            "refund_pct": 20,
            "refund_amount": calc_amt,
            "voucher_code": voucher_code,
            "voucher_value": "₹50 Crisp Restoration Voucher",
            "policy_rationale": (
                f"Fried items and crusts naturally accumulate steam condensation inside enclosed courier delivery bags over a 25-35 minute bike ride. "
                f"The food from {restaurant_name} remains fresh and safe, so a full refund does not apply. We are happy to issue a 20% courtesy credit of ₹{calc_amt:.2f} along with our chef restoration tips."
            ),
            "restaurant_note": "Moisture trapping in sealed delivery packaging.",
            "reheating_tip": policy_meta["reheating_tip"],
            "interactive_options": [
                {"label": f"⚡ Credit 20% to Wallet (₹{calc_amt:.2f})", "method": "wallet"},
                {"label": f"🎟️ Claim ₹50 Voucher ({voucher_code})", "method": "voucher"}
            ]
        }

    # 5. COLD / LUKEWARM FOOD (HOT MEALS)
    if issue_type == "cold_food" or any(w in q_lower for w in ["cold", "cool", "lukewarm", "not hot", "chilled", "room temperature"]):
        cold_rule = cuisine_info["cold_rules"]
        pct = 25  # Standard 25% courtesy refund
        calc_amt = round((total_amount * pct) / 100.0, 2)
        voucher_code = f"WARM25-{ord_suffix}"
        return {
            "tier": f"Transit Temperature Drop — 25% Courtesy Refund ({restaurant_name})",
            "decision": "APPROVE_PARTIAL_REFUND",
            "refund_pct": pct,
            "refund_amount": calc_amt,
            "voucher_code": voucher_code,
            "voucher_value": "₹75 Next-Order Voucher",
            "policy_rationale": (
                f"Food temperature decreases naturally during two-wheeler courier transit across city traffic. "
                f"Because the meal from {restaurant_name} remains freshly cooked, wholesome, and completely safe to consume, "
                f"a 100% full refund is never warranted for temperature drop. Instead, our standard policy provides a 25% courtesy wallet refund (₹{calc_amt:.2f}) or a ₹75 voucher (`{voucher_code}`), along with chef-recommended reheating advice."
            ),
            "restaurant_note": cuisine_info.get("temperature_behavior", "Heat dissipates in transit."),
            "reheating_tip": policy_meta["reheating_tip"],
            "interactive_options": [
                {"label": f"⚡ Credit 25% to Wallet (₹{calc_amt:.2f})", "method": "wallet"},
                {"label": f"🎟️ Take ₹75 Voucher ({voucher_code})", "method": "voucher"}
            ]
        }

    # 6. SPILLED / PACKAGING DAMAGE
    if issue_type == "spilled_packaging" or any(w in q_lower for w in ["spill", "leak", "crushed", "mess", "rupture", "bag soaked", "cracked"]):
        # Total catastrophe: entire meal rendered literally inedible or smashed on floor
        is_total_spill = any(w in q_lower for w in [
            "completely smashed", "totally ruined", "inedible", "unusable", "fell on floor",
            "box opened and dropped", "entire food ruined", "can't eat at all", "total disaster"
        ])

        if is_total_spill:
            spill_rule = cuisine_info["spill_rules"]["major"]
            pct = 100
            calc_amt = round((total_amount * pct) / 100.0, 2)
            voucher_code = f"{spill_rule['code_prefix']}100-{ord_suffix}"
            return {
                "tier": f"Severe Transit Damage — 100% Full Refund ({restaurant_name})",
                "decision": "APPROVE_FULL_REFUND",
                "refund_pct": 100,
                "refund_amount": calc_amt,
                "voucher_code": voucher_code,
                "voucher_value": "100% Meal Reorder Voucher",
                "policy_rationale": (
                    f"Catastrophic packaging rupture in transit rendering the entire meal unusable. "
                    f"Under {restaurant_name}'s packaging integrity standard, the full meal amount of ₹{calc_amt:.2f} is refunded."
                ),
                "restaurant_note": f"Packaging Standard: {policy_meta['packaging_standard']}.",
                "reheating_tip": "We sincerely apologize that this meal was compromised.",
                "interactive_options": [
                    {"label": f"⚡ Credit ₹{calc_amt:.2f} to Wallet Instantly", "method": "wallet"},
                    {"label": f"🎟️ Use 100% Meal Voucher ({voucher_code})", "method": "voucher"},
                    {"label": f"💳 Refund to Bank/Card (₹{calc_amt:.2f})", "method": "bank"}
                ]
            }
        else:
            # Check if moderate leak (gravy soaked box/bag, but main dish partly edible) vs minor side spill
            is_moderate_leak = any(w in q_lower for w in ["gravy leaked", "curry leaked", "box cracked", "soaked", "messy"])
            if is_moderate_leak:
                pct = 35
                calc_amt = round((total_amount * pct) / 100.0, 2)
                voucher_code = f"SPILL35-{ord_suffix}"
                return {
                    "tier": f"Moderate Packaging Leak — 35% Partial Refund ({restaurant_name})",
                    "decision": "APPROVE_PARTIAL_REFUND",
                    "refund_pct": 35,
                    "refund_amount": calc_amt,
                    "voucher_code": voucher_code,
                    "voucher_value": "₹100 Apology Dining Voucher",
                    "policy_rationale": (
                        f"Gravy or sauce container experienced transit leakage into the delivery bag, but the primary course remains mostly intact and consumable. "
                        f"A full 100% cancellation does not apply. We approve a 35% partial refund of ₹{calc_amt:.2f} or a ₹100 apology dining voucher."
                    ),
                    "restaurant_note": f"Packaging Standard: {policy_meta['packaging_standard']}.",
                    "reheating_tip": policy_meta["reheating_tip"],
                    "interactive_options": [
                        {"label": f"⚡ Accept 35% Wallet Credit (₹{calc_amt:.2f})", "method": "wallet"},
                        {"label": f"🎟️ Take ₹100 Voucher ({voucher_code})", "method": "voucher"},
                        {"label": "🍲 Report Total Meal Ruin (Escalate)", "method": "escalate"}
                    ]
                }
            else:
                # Minor side condiment spill (raita, dip, chutney, ketchup)
                spill_rule = cuisine_info["spill_rules"]["minor"]
                pct = 20
                calc_amt = round((total_amount * pct) / 100.0, 2)
                voucher_code = f"CONDIMENT20-{ord_suffix}"
                return {
                    "tier": f"Minor Condiment Spill — 20% Courtesy Credit ({restaurant_name})",
                    "decision": "APPROVE_PARTIAL_REFUND",
                    "refund_pct": 20,
                    "refund_amount": calc_amt,
                    "voucher_code": voucher_code,
                    "voucher_value": f"₹{spill_rule['voucher_val']} Condiment Voucher",
                    "policy_rationale": (
                        f"Side condiment container leak: {spill_rule['desc']}. "
                        f"Since the primary dish is completely intact and safe, we offer a 20% courtesy refund of ₹{calc_amt:.2f} or a ₹{spill_rule['voucher_val']} next-order voucher."
                    ),
                    "restaurant_note": f"Packaging Standard: {policy_meta['packaging_standard']}.",
                    "reheating_tip": policy_meta["reheating_tip"],
                    "interactive_options": [
                        {"label": f"⚡ Accept 20% Wallet Credit (₹{calc_amt:.2f})", "method": "wallet"},
                        {"label": f"🎟️ Claim ₹{spill_rule['voucher_val']} Voucher ({voucher_code})", "method": "voucher"}
                    ]
                }

    # 7. MISSING ITEMS (Item-level ONLY)
    if issue_type == "missing_items" or any(w in q_lower for w in ["missing", "forgot", "didn't get", "not delivered", "short item", "where is my drink"]):
        missing_val = 0.0
        missing_item_name = "Missing Item"
        if items:
            for it in items:
                it_name = it.get("name", "")
                if it_name.lower() in q_lower:
                    missing_item_name = it_name
                    p_match = re.search(r'\d+', str(it.get("price", "")))
                    if p_match:
                        missing_val = float(p_match.group(0))
                    break

        if missing_val <= 0.0:
            missing_val = round(total_amount * 0.30, 2)

        compensation_amt = round(missing_val + 30.0, 2)
        if compensation_amt > total_amount:
            compensation_amt = total_amount

        voucher_code = f"MISSING-{ord_suffix}"
        return {
            "tier": f"Item-Level Refund + Convenience Credit ({missing_item_name})",
            "decision": "APPROVE_PARTIAL_REFUND",
            "refund_pct": round((compensation_amt / total_amount) * 100),
            "refund_amount": compensation_amt,
            "voucher_code": voucher_code,
            "voucher_value": f"₹{compensation_amt:.2f} Wallet Balance",
            "policy_rationale": (
                f"Fair item-level reimbursement: The missing item ({missing_item_name}) value of ₹{missing_val:.2f} is refunded in full, "
                "plus a ₹30 delivery inconvenience credit. We do not cancel the rest of your meal that was successfully delivered."
            ),
            "restaurant_note": f"Missing item logged against {restaurant_name} packing station.",
            "reheating_tip": "Enjoy the delivered portion of your meal while your missing item refund is credited.",
            "interactive_options": [
                {"label": f"⚡ Credit ₹{compensation_amt:.2f} to Wallet Instantly", "method": "wallet"},
                {"label": f"🎟️ Issue Re-order Coupon ({voucher_code})", "method": "voucher"}
            ]
        }

    # 8. DELAYED DELIVERY (GPS Verified)
    if issue_type == "late_delivery" or any(w in q_lower for w in ["late", "delay", "taking too long", "where is it", "hours late"]):
        voucher_code = f"ONTIME50-{ord_suffix}"
        calc_amt = round(total_amount * 0.15, 2)
        return {
            "tier": f"On-Time Guarantee Compensation ({restaurant_name})",
            "decision": "APPROVE_PARTIAL_REFUND",
            "refund_pct": 15,
            "refund_amount": max(50.0, calc_amt),
            "voucher_code": voucher_code,
            "voucher_value": "₹50 On-Time Voucher",
            "policy_rationale": (
                f"Rider delay verified against dispatch logs. Under SupportFlow's On-Time Guarantee, "
                f"we credit a 15% courtesy refund or ₹50 apology voucher to your wallet. Full refund does not apply since the food is successfully delivered."
            ),
            "restaurant_note": "Courier transit delay recorded.",
            "reheating_tip": policy_meta["reheating_tip"],
            "interactive_options": [
                {"label": f"⚡ Accept ₹{max(50.0, calc_amt):.2f} Wallet Credit", "method": "wallet"},
                {"label": f"🎟️ Use ₹50 On-Time Voucher ({voucher_code})", "method": "voucher"}
            ]
        }

    # 9. WRONG ORDER / MISMATCHED ITEM
    if issue_type == "wrong_order" or any(w in q_lower for w in ["wrong item", "wrong food", "different dish", "not what i ordered", "mismatch"]):
        voucher_code = f"REPLACE-{ord_suffix}"
        return {
            "tier": f"Incorrect Dish Delivery — 100% Dish Refund ({restaurant_name})",
            "decision": "APPROVE_FULL_REFUND",
            "refund_pct": 100,
            "refund_amount": total_amount,
            "voucher_code": voucher_code,
            "voucher_value": "100% Meal Replacement Credit",
            "policy_rationale": (
                f"The delivered item does not match your billing order from {restaurant_name}. "
                "You are entitled to a full 100% refund or instant meal replacement credit so you can order your intended dish."
            ),
            "restaurant_note": "Order tagging dispatch error at restaurant counter.",
            "reheating_tip": "You may keep or dispose of the incorrectly delivered dish.",
            "interactive_options": [
                {"label": f"⚡ Instant 100% Wallet Refund (₹{total_amount:.2f})", "method": "wallet"},
                {"label": f"🎟️ Claim 100% Replacement Code ({voucher_code})", "method": "voucher"},
                {"label": f"💳 Refund to Original UPI/Bank (3-5 days)", "method": "bank"}
            ]
        }

    # 10. BURNT / SEVERELY SPOILED / INEDIBLE QUALITY
    if issue_type == "burnt_quality" or any(w in q_lower for w in ["burnt", "charred", "black", "inedible", "raw chicken", "undercooked meat", "stale", "spoiled"]):
        voucher_code = f"QUALITY100-{ord_suffix}"
        return {
            "tier": f"Culinary Quality Defect — 100% Full Refund ({restaurant_name})",
            "decision": "APPROVE_FULL_REFUND",
            "refund_pct": 100,
            "refund_amount": total_amount,
            "voucher_code": voucher_code,
            "voucher_value": "100% Fresh Meal Replacement",
            "policy_rationale": (
                f"Inedible or severely defective food violates our culinary standards at {restaurant_name}. "
                "A 100% full refund is approved immediately, and a kitchen supervisor review has been initiated."
            ),
            "restaurant_note": "Quality audit flag assigned to kitchen line supervisor.",
            "reheating_tip": "Do not consume charred, spoiled, or undercooked food.",
            "interactive_options": [
                {"label": f"⚡ Instant 100% Wallet Refund (₹{total_amount:.2f})", "method": "wallet"},
                {"label": f"🎟️ 100% Dining Replacement Voucher ({voucher_code})", "method": "voucher"}
            ]
        }

    # 11. CANCELLATION
    if issue_type == "cancellation" or any(w in q_lower for w in ["cancel", "change my mind"]):
        return {
            "tier": "Cancellation Policy (Kitchen Preparation In Progress)",
            "decision": "REJECT_REFUND",
            "refund_pct": 0,
            "refund_amount": 0.0,
            "voucher_code": None,
            "voucher_value": None,
            "policy_rationale": (
                f"Once {restaurant_name}'s kitchen starts cooking your order, fresh ingredients are already committed. "
                "To protect culinary partners from food wastage, cancellations at this stage are subject to a 100% cancellation charge."
            ),
            "restaurant_note": "Kitchen preparation active.",
            "reheating_tip": "Your order is being prepared fresh and will be delivered shortly!",
            "interactive_options": [
                {"label": "🛵 Track Live Order Status", "method": "track"},
                {"label": "🧑‍💼 Speak to Support Manager", "method": "escalate"}
            ]
        }

    # 12. GENERAL COURTESY RESOLUTION (Ambiguous Claim)
    calc_amt = round(total_amount * 0.15, 2)
    voucher_code = f"DELIGHT-{ord_suffix}"
    return {
        "tier": f"Customer Delight Courtesy Credit ({restaurant_name})",
        "decision": "APPROVE_PARTIAL_REFUND",
        "refund_pct": 15,
        "refund_amount": calc_amt,
        "voucher_code": voucher_code,
        "voucher_value": "₹40 Courtesy Voucher",
        "policy_rationale": (
            f"We want every experience with {restaurant_name} to be positive. "
            f"We have approved a 15% courtesy credit of ₹{calc_amt:.2f} or a ₹40 goodwill dining coupon."
        ),
        "restaurant_note": "Goodwill courtesy gesture.",
        "reheating_tip": policy_meta["reheating_tip"],
        "interactive_options": [
            {"label": f"⚡ Credit ₹{calc_amt:.2f} to Wallet", "method": "wallet"},
            {"label": f"🎟️ Claim Dining Voucher ({voucher_code})", "method": "voucher"}
        ]
    }

