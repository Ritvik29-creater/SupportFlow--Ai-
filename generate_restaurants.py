import os

restaurants = [
    "The Great Indian Dhaba - North Indian, Mughlai - 4.5/5",
    "Spicy Corner - Street Food, Fast Food - 4.2/5",
    "Burger Hub - American, Fast Food - 4.0/5",
    "Pizza Express - Italian, Pizza - 4.3/5",
    "Sushi Train - Japanese, Sushi - 4.7/5",
    "Taco Fiesta - Mexican - 4.1/5",
    "Vegan Delights - Healthy, Vegan - 4.6/5",
    "Steakhouse Grill - Continental, Steak - 4.4/5",
    "Pasta Paradise - Italian - 4.2/5",
    "Wok This Way - Chinese, Asian - 4.3/5",
    "Biryani Central - Biryani, Mughlai - 4.8/5",
    "Kebab King - North Indian, Kebab - 4.5/5",
    "Dosa Diner - South Indian - 4.4/5",
    "Dimsum Stop - Chinese - 4.1/5",
    "Falafel Fresh - Middle Eastern - 4.3/5",
    "The Salad Bar - Healthy - 4.0/5",
    "Curry House - Indian - 4.2/5",
    "Seafood Shenanigans - Seafood - 4.5/5",
    "Waffle Wonderland - Desserts, Beverages - 4.6/5",
    "Ice Cream Social - Desserts - 4.7/5",
    "The Bake House - Bakery, Desserts - 4.4/5",
    "Coffee Culture - Cafe, Beverages - 4.3/5",
    "Tea Time - Beverages, Snacks - 4.1/5",
    "Smoothie Station - Healthy, Beverages - 4.2/5",
    "Wrap It Up - Fast Food, Wraps - 4.0/5",
    "Sandwich Shop - Fast Food - 4.1/5",
    "Fried Chicken Frenzy - American, Fast Food - 4.3/5",
    "Hot Dog Haven - Fast Food - 3.9/5",
    "Noodle Nexus - Asian - 4.2/5",
    "Ramen Realm - Japanese - 4.5/5",
    "Pho Palace - Vietnamese - 4.4/5",
    "Thai Time - Thai - 4.3/5",
    "Mediterranean Magic - Mediterranean - 4.6/5",
    "Spanish Tapas - Spanish - 4.5/5",
    "French Connection - French - 4.7/5",
    "Greek Grill - Greek - 4.4/5",
    "Peruvian Plates - Peruvian - 4.2/5",
    "Brazilian BBQ - Brazilian - 4.5/5",
    "Argentine Asado - Argentine - 4.6/5",
    "Korean BBQ - Korean - 4.7/5",
    "Ethiopian Eats - Ethiopian - 4.3/5",
    "Moroccan Meals - Moroccan - 4.4/5",
    "Caribbean Cuisine - Caribbean - 4.2/5",
    "Jamaican Jerk - Jamaican - 4.3/5",
    "Soul Food Kitchen - American, Soul Food - 4.5/5",
    "Cajun Corner - Cajun, Creole - 4.4/5",
    "Tex-Mex Tavern - Tex-Mex - 4.1/5",
    "Barbecue Barn - BBQ - 4.3/5",
    "Breakfast Club - Breakfast, Cafe - 4.6/5",
    "Brunch Spot - Cafe, Continental - 4.5/5"
]

content = "# Partner Restaurants\n\nWe currently partner with the following 50 top-rated restaurants to ensure high quality and fast delivery. If a customer inquires about our restaurant database or asks about food options, use this list:\n\n"
for i, r in enumerate(restaurants, 1):
    content += f"## {i}. {r}\n- Policy: Standard delivery in 30-45 minutes.\n- Rating: Verified.\n- Refund Policy: Covered under SupportFlow Guarantee.\n\n"

with open("D:/Downloads/Langgraph-Customer-Support-Multi-Agent-main/Langgraph-Customer-Support-Multi-Agent-main/data/docs/restaurants/50_restaurants.md", "w", encoding="utf-8") as f:
    f.write(content)

print("Created 50_restaurants.md")
