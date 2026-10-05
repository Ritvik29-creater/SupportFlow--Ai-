"""
SupportFlow AI — Restaurant & Culinary Service
Provides direct database lookups for all 90+ restaurants, signature dishes,
and extensive culinary recipes/ingredients knowledge for the multi-agent chatbot.
"""
from typing import List, Dict, Any, Optional
from database.connection import SessionLocal
from database.models import Restaurant, MenuItem

# Authentic recipe & culinary knowledge base for popular dishes
CULINARY_RECIPES = {
    "biryani": {
        "name": "Dum Biryani (Chicken & Mutton)",
        "origin": "Hyderabadi & Mughlai Royal Cuisine",
        "key_ingredients": [
            "Aged Long-grain Basmati Rice",
            "Marinated Chicken/Mutton (Yogurt, Ginger-Garlic, Kashmiri Chilli, Garam Masala)",
            "Kashmiri Saffron soaked in warm milk",
            "Fried Golden Onions (Birista)",
            "Fresh Mint & Coriander leaves",
            "Pure Ghee & Rose/Kewra Water",
            "Whole Spices: Green Cardamom, Cloves, Cinnamon, Star Anise, Shahi Jeera"
        ],
        "cooking_process": (
            "1. Marinate meat overnight in spiced curd, ginger-garlic paste, and crushed fried onions.\n"
            "2. Par-boil basmati rice with whole aromatic spices until 70% cooked.\n"
            "3. Layer the marinated meat and parboiled rice alternately in a heavy-bottomed handi.\n"
            "4. Drizzle generous saffron milk, melted desi ghee, mint, and fried onions on top.\n"
            "5. Seal the vessel airtight with wheat dough ('Dum') and slow-cook on low flame for 45 minutes.\n"
            "6. The trapped steam cooks the meat in its own juices while perfuming every grain of rice."
        ),
        "flavor_profile": "Aromatic, rich, mildly spiced to fiery, complex layering of whole spices.",
        "dietary": "Halal meat, gluten-free, rich in protein."
    },
    "pizza": {
        "name": "Neapolitan Margherita D.O.C Pizza",
        "origin": "Naples, Italy",
        "key_ingredients": [
            "Tipo 00 Italian Flour (high protein, fine grind)",
            "San Marzano D.O.P Italian Plum Tomatoes",
            "Fresh Mozzarella di Bufala (Buffalo Mozzarella) or Fior di Latte",
            "Fresh Genovese Basil Leaves",
            "Cold-pressed Extra Virgin Olive Oil",
            "Fine Sea Salt & Active Dry Yeast"
        ],
        "cooking_process": (
            "1. Ferment the dough for 24-48 hours cold-ferment to develop complex airy bubbles (cornicione).\n"
            "2. Hand-stretch the dough gently without a rolling pin to preserve crust air pockets.\n"
            "3. Spread crushed raw San Marzano tomatoes with a pinch of sea salt.\n"
            "4. Top with torn fresh buffalo mozzarella and a drizzle of extra virgin olive oil.\n"
            "5. Bake in a wood-fired oven at 450°C-485°C (850°F) for just 60 to 90 seconds.\n"
            "6. Garnish with fresh basil leaves immediately after exiting the oven."
        ),
        "flavor_profile": "Smoky leopard-spotted charred crust, sweet-acidic tomato burst, creamy melted cheese.",
        "dietary": "Vegetarian, high carbohydrate, customizable with vegan cheese."
    },
    "butter chicken": {
        "name": "Murgh Makhani (Butter Chicken)",
        "origin": "Delhi, Moti Mahal (1950s)",
        "key_ingredients": [
            "Boneless Chicken Thighs (tandoor charred)",
            "Ripe Roma/San Marzano Tomatoes (pureed)",
            "Salted Amul Butter & Double Cream",
            "Cashew Nut Paste (for velvet gloss)",
            "Kasuri Methi (sun-dried fenugreek leaves)",
            "Honey / Dash of Sugar (for balance)",
            "Degi Mirch (for vibrant red color without harsh heat)"
        ],
        "cooking_process": (
            "1. Marinate chicken in mustard oil, hung curd, Kashmiri red chilli, and tandoori spices.\n"
            "2. Skewer and roast in a tandoor at high heat until smoky and charred at the edges.\n"
            "3. Simmer fresh tomato puree with whole spices, degi mirch, and butter for 40 minutes.\n"
            "4. Blend smooth and strain to create the silkiest 'makhani' velvet base.\n"
            "5. Stir in cashew paste, double cream, honey, and crushed toasted kasuri methi.\n"
            "6. Toss in the smoked tandoori chicken chunks and finish with another dollop of cold butter."
        ),
        "flavor_profile": "Creamy, buttery, sweet-tangy with subtle smokiness and herbaceous fenugreek aroma.",
        "dietary": "High protein, gluten-free, rich in healthy fats."
    },
    "dal makhani": {
        "name": "Dal Bukhara / Dal Makhani",
        "origin": "Punjab & Northwest Frontier",
        "key_ingredients": [
            "Sabut Urad Dal (Whole Black Gram)",
            "Rajma (Red Kidney Beans)",
            "Fresh Tomato Puree & Ginger-Garlic Paste",
            "Pure White Butter (Makhan) & Fresh Cream",
            "Toasted Kasuri Methi & Kashmiri Red Chilli"
        ],
        "cooking_process": (
            "1. Soak black urad dal and kidney beans for 12 hours, washing thoroughly.\n"
            "2. Slow simmer on low charcoal fire for 16-18 hours until dal is soft and creamy naturally.\n"
            "3. Temper with ginger-garlic paste, fresh tomato reduction, and degi mirch.\n"
            "4. Continuously mash with the back of a wooden ladle while adding white butter and cream.\n"
            "5. Smoke using hot charcoal and ghee ('Dhungar method') for that authentic Bukhara taste."
        ),
        "flavor_profile": "Earthy, velvety, smoky, rich, and comforting.",
        "dietary": "Vegetarian, high fiber, high plant-based protein."
    },
    "burger": {
        "name": "Gourmet Smashed Truffle & Cheese Burger",
        "origin": "American Gastropub",
        "key_ingredients": [
            "Brioche Bun (toasted with butter)",
            "Double Smash Patty (Prime Beef / Lamb or Crispy Portobello Mushroom)",
            "Aged English Cheddar & Swiss Gruyere",
            "Black Truffle Aioli / Truffle Mayo",
            "Caramelized Balsamic Onions",
            "Crispy Gherkins / Dill Pickles"
        ],
        "cooking_process": (
            "1. Ball the chilled patty meat and place on a roaring hot cast-iron skillet (250°C).\n"
            "2. Smash paper-thin with a heavy burger press to create ultra-crispy caramelized lacy edges.\n"
            "3. Season aggressively with kosher salt and black pepper; flip once after 2 minutes.\n"
            "4. Top immediately with cheddar, cover with cloche and splash water to steam melt.\n"
            "5. Spread truffle aioli on both halves of toasted brioche; layer with pickles and caramelized onions."
        ),
        "flavor_profile": "Savory umami explosion, crispy charred edges, gooey cheese, buttery brioche sweetness.",
        "dietary": "Available in vegetarian (Portobello/Paneer) or chicken/lamb options."
    },
    "dosa": {
        "name": "Mysore Masala Dosa",
        "origin": "Mysore, Karnataka, South India",
        "key_ingredients": [
            "Fermented Rice & Urad Dal Batter (3:1 ratio with fenugreek seeds)",
            "Spicy Red Garlic & Byadgi Chilli Chutney",
            "Aloo Masala (Boiled potatoes, mustard seeds, curry leaves, onions, turmeric)",
            "Pure Desi Ghee / Butter",
            "Coconut Chutney & Piping Hot Drumstick Sambar"
        ],
        "cooking_process": (
            "1. Ferment batter naturally for 14 hours until aerated and slightly sour.\n"
            "2. Pour a ladle onto a hot cast-iron tawa and swirl thin from inside out.\n"
            "3. Spread generous spoonfuls of red chilli-garlic chutney across the inner surface.\n"
            "4. Drizzle pure ghee around edges until the crepe turns deep golden brown and crispy.\n"
            "5. Place spiced potato bhaji in the center, fold into a cylinder, and serve sizzling hot."
        ),
        "flavor_profile": "Crispy golden exterior, soft spiced interior, fiery garlic punch balanced by cool coconut.",
        "dietary": "Vegetarian, vegan-friendly (with oil instead of ghee), gluten-free, probiotics from fermentation."
    },
    "tiramisu": {
        "name": "Classic Venetian Tiramisu",
        "origin": "Veneto, Italy",
        "key_ingredients": [
            "Italian Savoiardi (Ladyfinger biscuits)",
            "Fresh Galbani Mascarpone Cheese",
            "Pasteurized Egg Yolks & Sugar (Zabaione base)",
            "Freshly Brewed Strong Espresso Coffee",
            "Marsala Wine or Kahlua (optional)",
            "Unsweetened Dutch-processed Cocoa Powder"
        ],
        "cooking_process": (
            "1. Whip egg yolks with caster sugar over a bain-marie until pale and ribbon-like.\n"
            "2. Fold in softened mascarpone cheese gently until silky and lump-free.\n"
            "3. Briefly dip savoiardi into cooled espresso (1 second each side; do not drench).\n"
            "4. Layer soaked biscuits at the bottom of the dish, spread half the mascarpone cream.\n"
            "5. Repeat second layer of biscuits and cream; refrigerate minimum 6 hours to set.\n"
            "6. Dust generously with fine bitter cocoa powder right before serving."
        ),
        "flavor_profile": "Velvety creaminess, bold coffee bitterness, tender sponge texture, chocolate finish.",
        "dietary": "Vegetarian, contains dairy & caffeine."
    }
}


def search_restaurants_and_dishes(query: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Search for matching restaurants, cuisines, and signature dishes in SQLite."""
    db = SessionLocal()
    try:
        q = f"%{query.strip().lower()}%"
        # Search restaurants
        rests = db.query(Restaurant).filter(
            (Restaurant.name.ilike(q)) |
            (Restaurant.cuisine_type.ilike(q)) |
            (Restaurant.address.ilike(q))
        ).limit(limit).all()

        results = []
        for r in rests:
            items = db.query(MenuItem).filter(MenuItem.restaurant_id == r.id).all()
            results.append({
                "type": "restaurant",
                "id": r.id,
                "name": r.name,
                "cuisine": r.cuisine_type,
                "address": r.address,
                "rating": r.rating,
                "delivery_time": f"{r.delivery_time_min} mins",
                "price_for_two": f"₹{int(r.min_order_amount * 2.5)} for two" if r.min_order_amount else "₹350 for two",
                "dishes": [
                    {
                        "name": it.name,
                        "price": f"₹{it.price}",
                        "is_veg": it.is_veg,
                        "desc": it.description
                    }
                    for it in items
                ]
            })

        # Also search dishes
        dishes = db.query(MenuItem).filter(
            (MenuItem.name.ilike(q)) |
            (MenuItem.description.ilike(q)) |
            (MenuItem.category.ilike(q))
        ).limit(limit).all()

        for d in dishes:
            r = db.query(Restaurant).filter(Restaurant.id == d.restaurant_id).first()
            if r and not any(res.get("name") == r.name for res in results):
                results.append({
                    "type": "dish_match",
                    "matched_dish": d.name,
                    "dish_price": f"₹{d.price}",
                    "dish_desc": d.description,
                    "is_veg": d.is_veg,
                    "restaurant_name": r.name,
                    "cuisine": r.cuisine_type,
                    "rating": r.rating,
                    "address": r.address,
                })

        return results
    except Exception as e:
        print(f"[Restaurant Service Search Error] {e}")
        return []
    finally:
        db.close()


def get_restaurant_catalog_summary(limit: int = 15) -> List[Dict[str, Any]]:
    """Get a quick summary of top-rated restaurants across various cuisines for recommendations."""
    db = SessionLocal()
    try:
        rests = db.query(Restaurant).order_by(Restaurant.rating.desc()).limit(limit).all()
        catalog = []
        for r in rests:
            items = db.query(MenuItem).filter(MenuItem.restaurant_id == r.id).all()
            catalog.append({
                "name": r.name,
                "cuisine": r.cuisine_type,
                "location": r.address,
                "rating": r.rating,
                "delivery_time": f"{r.delivery_time_min} mins",
                "signature_dishes": [it.name for it in items[:3]]
            })
        return catalog
    except Exception as e:
        print(f"[Restaurant Catalog Error] {e}")
        return []
    finally:
        db.close()


def find_recipe_knowledge(query: str) -> Optional[Dict[str, Any]]:
    """Check if the query matches our in-depth culinary recipe database."""
    q_lower = query.lower()
    for key, data in CULINARY_RECIPES.items():
        if key in q_lower or any(word in q_lower for word in data["name"].lower().split()):
            return data
    return None
