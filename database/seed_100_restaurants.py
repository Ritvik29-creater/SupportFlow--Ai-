"""
Seed 100 Realistic Restaurants and Menus for SupportFlow AI
Creates 100 top-rated restaurants across 10 cuisine categories with 3-5 signature items each.
"""
import uuid
import random
from database.connection import SessionLocal, create_tables
from database.models import Restaurant, MenuItem

CATEGORIES = [
    {
        "cuisine": "Biryani & Mughlai",
        "emoji": "🍗",
        "restaurants": [
            ("Meghana Foods", "Koramangala, 5th Block", 4.8, 30, [
                ("Special Chicken Biryani", 320.0, "Spicy Andhra-style biryani with tender chicken pieces and aromatic rice", True, "🍗", False),
                ("Boneless Chicken 65 Biryani", 340.0, "Signature crisp chicken 65 served over spicy biryani rice", True, "🍛", False),
                ("Paneer Biryani", 280.0, "Richly spiced basmati rice layered with soft marinated paneer cubes", True, "🍚", True),
                ("Apollo Fish", 350.0, "Crisp battered fish tossed in curry leaves and Andhra spices", False, "🐟", False),
            ]),
            ("Behrouz Biryani", "Indiranagar, 100ft Road", 4.7, 35, [
                ("Dum Gosht Biryani", 420.0, "Slow-cooked mutton layered with saffron rice and fragrant spices", True, "🍖", False),
                ("Subz-e-Biryani", 290.0, "Farm-fresh vegetables and paneer in royal spices", True, "🥦", True),
                ("Murgh Tikka Biryani", 360.0, "Charcoal grilled chicken tikka in spiced basmati rice", True, "🍗", False),
                ("Gulab Jamun with Rabdi", 120.0, "Warm golden dumplings in saffron rabdi", False, "🍯", True),
            ]),
            ("Paradise Biryani", "MG Road, Central", 4.6, 25, [
                ("Royal Hyderabadi Chicken Dum Biryani", 310.0, "Traditional slow dum cooked Hyderabadi biryani with mirchi ka salan", True, "🍲", False),
                ("Mutton Special Biryani", 430.0, "Tender mutton pieces infused with shahi spices", True, "🍖", False),
                ("Chicken Reshmi Kebab", 280.0, "Silky smooth melt-in-mouth chicken kebabs", False, "🍢", False),
            ]),
            ("Bikkgane Biryani", "HSR Layout, Sector 2", 4.5, 30, [
                ("Hyderabadi Chicken Biryani", 295.0, "Authentic spicy dum biryani", True, "🍗", False),
                ("Chicken Keema Biryani", 330.0, "Spiced minced chicken cooked with aromatic basmati rice", True, "🍛", False),
                ("Egg Biryani", 240.0, "Boiled spiced eggs roasted and layered in biryani rice", True, "🥚", False),
            ]),
            ("Biryani By Kilo", "Whitefield, ITPL Main Rd", 4.7, 40, [
                ("Handi Chicken Dum Biryani (1kg)", 650.0, "Delivered in traditional earthen clay handi", True, "🏺", False),
                ("Kathal (Jackfruit) Biryani", 340.0, "Tender jackfruit cooked in Awadhi spices", True, "🍲", True),
                ("Galouti Kebab", 380.0, "Melt-in-mouth Lucknowi kebabs with Mughlai paratha", False, "🥩", False),
            ]),
            ("Nizam's Royal Kitchen", "Frazer Town", 4.4, 30, [
                ("Murgh Malai Biryani", 330.0, "Creamy mild chicken biryani infused with cardamom", True, "🍗", False),
                ("Shahi Paneer Dum Biryani", 280.0, "Paneer in rich cashew gravy and saffron rice", True, "🍚", True),
                ("Seekh Kebab Platter", 360.0, "Trio of chicken, mutton, and vegetable seekh kebabs", False, "🍢", False),
            ]),
            ("Sharief Bhai", "Koramangala, 7th Block", 4.6, 25, [
                ("Murgh Sofiyani Biryani", 320.0, "White saffron biryani with fragrant mild spices", True, "🍲", False),
                ("Gosht Haleem", 260.0, "Slow-cooked meat and lentils pounded with ghee and spices", False, "🥣", False),
                ("Pathar Ka Gosht", 340.0, "Lamb fillets grilled on heated granite stone", False, "🥩", False),
            ]),
            ("Aasife Biryani", "Marathahalli", 4.3, 35, [
                ("Chennai Dindigul Chicken Biryani", 280.0, "Seeraga samba rice cooked with country chicken", True, "🍗", False),
                ("Chicken Sukka", 240.0, "Dry roasted spicy chicken with coconut slivers", False, "🍛", False),
                ("Mutton Chops Fry", 360.0, "Pan-seared tender mutton chops", False, "🍖", False),
            ]),
            ("Empire Restaurant", "Church Street", 4.5, 20, [
                ("Empire Special Chicken Ghee Rice", 250.0, "Fluffy ghee rice served with spicy roast chicken", True, "🍗", False),
                ("Coin Parotta with Chicken Curry", 220.0, "Flaky Kerala parottas with rich coconut chicken curry", True, "🫓", False),
                ("Empire Jumbo Shawarma", 150.0, "Loaded grilled chicken shawarma in rumali roti", False, "🌯", False),
            ]),
            ("Nagarjuna Andhra Style", "Residency Road", 4.8, 30, [
                ("Andhra Chicken Biryani", 330.0, "Fiery green chilli spiced biryani", True, "🍗", False),
                ("Nagarjuna Roast Chicken", 290.0, "Spicy Andhra dry roast with curry leaves", False, "🍗", False),
                ("Gongura Mutton Biryani", 410.0, "Tangy sorrel leaf infused mutton biryani", True, "🍛", False),
            ]),
        ]
    },
    {
        "cuisine": "Pizza & Italian",
        "emoji": "🍕",
        "restaurants": [
            ("Napoli Woodfired Pizza", "Indiranagar", 4.9, 30, [
                ("Margherita D.O.C Pizza", 399.0, "San Marzano tomatoes, fresh buffalo mozzarella, basil", True, "🍕", True),
                ("Truffle & Wild Mushroom Pizza", 520.0, "Shiitake mushrooms, truffle oil, fior di latte", True, "🍄", True),
                ("Spicy Pepperoni & Jalapeno", 499.0, "Cured pork pepperoni, spicy jalapenos, hot honey", True, "🍕", False),
                ("Tiramisu Classico", 240.0, "Espresso soaked savoiardi with mascarpone cream", False, "🍰", True),
            ]),
            ("Domino's Pizza", "Sector 4, Main Rd", 4.4, 25, [
                ("Farmhouse Pizza", 349.0, "Delightful combo of onion, capsicum, tomato & mushroom", True, "🍕", True),
                ("Peppy Paneer Pizza", 389.0, "Flavorful trio of juicy paneer, crisp capsicum with spicy red paprika", True, "🧀", True),
                ("Chicken Dominator", 499.0, "Loaded with double pepper barbecue chicken, peri-peri chicken, grilled chicken", True, "🍗", False),
                ("Choco Lava Cake", 109.0, "Molten chocolate filled warm cake", False, "🍫", True),
            ]),
            ("Pizza Hut", "Forum Mall, Koramangala", 4.3, 30, [
                ("Veggie Supreme Stuffed Crust", 449.0, "Cheese stuffed crust with black olives, onions, and sweet corn", True, "🍕", True),
                ("Tandoori Paneer Pizza", 399.0, "Indian spiced paneer with red paprika and mint mayo", True, "🧀", True),
                ("Chicken Pepper Crunch", 459.0, "Crispy chicken popcorn tossed with peppers and mozzarella", True, "🍗", False),
                ("Garlic Breadsticks with Dip", 149.0, "Fresh baked breadsticks with creamy jalapeno dip", False, "🥖", True),
            ]),
            ("Tossin Pizza", "Jayanagar", 4.7, 35, [
                ("Peri Peri Chicken Gourmet Pizza", 480.0, "Spicy peri peri sauce with herb roasted chicken", True, "🍕", False),
                ("Four Cheese Bianco", 460.0, "Mozzarella, cheddar, gorgonzola and parmesan", True, "🧀", True),
                ("Smoked Salmon & Capers", 590.0, "Norwegian smoked salmon, dill, and capers", True, "🐟", False),
            ]),
            ("Brik Oven", "Church Street", 4.8, 30, [
                ("The Bird Pizza", 490.0, "Smoked chicken, crispy bacon, caramelized onions", True, "🍕", False),
                ("Popeye & Olive Oyl", 430.0, "Garlic spinach, sundried tomatoes, creamy feta", True, "🥗", True),
                ("Nutella & Waffles Calzone", 280.0, "Folded pizza pocket oozing with melted Nutella", False, "🥞", True),
            ]),
            ("Mojo Pizza", "Bellandur", 4.5, 25, [
                ("2X Toppings Big Pizza", 399.0, "Double toppings with double cheese", True, "🍕", True),
                ("Paneer Tikka Burst", 379.0, "Tandoori paneer with spicy red chillies", True, "🧀", True),
                ("BBQ Chicken Extravaganza", 449.0, "Smoky barbecue chicken chunks with golden corn", True, "🍗", False),
            ]),
            ("Chianti Italian Restaurant", "Koramangala", 4.7, 40, [
                ("Penne All'Arrabbiata", 390.0, "Spicy garlic tomato sauce with parmesan", True, "🍝", True),
                ("Spaghetti Carbonara", 480.0, "Creamy egg yolk sauce with crispy pancetta", True, "🍝", False),
                ("Lasagna Bolognese", 520.0, "Layered pasta with slow-cooked minced meat ragu", True, "🥘", False),
            ]),
            ("Little Italy", "Indiranagar", 4.5, 30, [
                ("Pizza Sicilia", 440.0, "Sun-dried tomatoes, pickled onions, mozzarella and capers", True, "🍕", True),
                ("Pasta Del Barone", 420.0, "Penne in creamy pink sauce with broccoli and mushrooms", True, "🍝", True),
                ("Bruschetta al Pomodoro", 240.0, "Toasted country bread topped with ripe tomatoes and garlic", False, "🥖", True),
            ]),
            ("California Burrito & Pizza Co.", "HSR Layout", 4.4, 25, [
                ("Crispy Thin Crust Chicken Pizza", 360.0, "Herb chicken and roasted peppers", True, "🍕", False),
                ("Creamy Pesto Penne", 340.0, "Fresh basil pesto with pine nuts and cherry tomatoes", True, "🍝", True),
            ]),
            ("Oven Story Pizza", "Sarjapur Road", 4.3, 30, [
                ("Middle Eastern Supreme Pizza", 420.0, "Loaded with peri peri chicken and golden corn", True, "🍕", False),
                ("Picante Paneer Pizza", 360.0, "Fiery chipotle cheese base with spiced paneer", True, "🧀", True),
            ]),
        ]
    },
    {
        "cuisine": "Burgers & American Fast Food",
        "emoji": "🍔",
        "restaurants": [
            ("Artisan Burger Co.", "Lavelle Road", 4.8, 25, [
                ("Double Truffle Smash Burger", 360.0, "Two smashed beef patties, truffle mayo, aged cheddar, potato bun", True, "🍔", False),
                ("Crispy Buttermilk Chicken Burger", 310.0, "24-hr brined crispy chicken thigh, chipotle slaw, pickles", True, "🍗", False),
                ("Seasoned Waffle Fries", 140.0, "Crispy criss-cross fries tossed in house cajun spice", False, "🍟", True),
                ("Salted Caramel Thickshake", 190.0, "Rich vanilla ice cream blended with homemade salted caramel", False, "🥤", True),
            ]),
            ("Burger King", "Koramangala 80ft Rd", 4.4, 20, [
                ("Crispy Veg Burger Combo", 169.0, "Crispy veg patty burger with fries and beverage", True, "🍔", True),
                ("Whopper Chicken", 219.0, "Flame-grilled chicken patty with crisp lettuce and mayo", True, "🍔", False),
                ("BK Chicken Fries", 139.0, "Tender chicken in crispy fry shape with dip", False, "🍟", False),
            ]),
            ("McDonald's", "Commercial Street", 4.3, 20, [
                ("McSpicy Chicken Burger", 199.0, "Tender and juicy chicken patty coated in spicy batter", True, "🍔", False),
                ("McAloo Tikki Burger", 65.0, "Potato and peas patty infused with signature spices", True, "🥔", True),
                ("World Famous Fries (L)", 125.0, "Golden crispy potato fries", False, "🍟", True),
                ("McFlurry Oreo", 115.0, "Soft vanilla soft serve swirled with crunchy Oreo bits", False, "🍦", True),
            ]),
            ("Leon's Burgers & Wings", "Indiranagar", 4.7, 25, [
                ("Leon's Signature Jumbo Burger", 320.0, "Crispy chicken breast with peri peri glaze and jalapenos", True, "🍔", False),
                ("Fiery BBQ Wings (6 Pcs)", 240.0, "Crispy chicken wings smothered in smoky barbecue sauce", False, "🍗", False),
                ("Loaded Cheesy Fries", 180.0, "Fries topped with warm cheese sauce and jalapeño bits", False, "🍟", True),
            ]),
            ("Truffles", "St. Marks Road", 4.8, 30, [
                ("All American Cheese Burger", 280.0, "Juicy patty, melted cheddar, lettuce, gherkins", True, "🍔", False),
                ("Tandoori Chicken Burger", 240.0, "Tandoori chicken steak with mint mayonnaise", True, "🍔", False),
                ("Ferrero Rocher Shake", 210.0, "Decadent thick shake topped with chocolate shavings", False, "🥤", True),
            ]),
            ("Wendy's Burgers", "HSR Layout", 4.3, 25, [
                ("Spicy Paneer Crunch Burger", 199.0, "Spiced paneer slice in toasted brioche bun", True, "🍔", True),
                ("Baconator Style Chicken Burger", 289.0, "Crispy chicken with smoked chicken strips and cheese", True, "🍔", False),
                ("Chilli Cheese Fries", 139.0, "Crispy fries with warm melted cheese and green chillies", False, "🍟", True),
            ]),
            ("KFC", "Brigade Road", 4.4, 20, [
                ("Hot & Crispy Chicken (4 Pcs)", 449.0, "Signature 11 secret herbs and spices crispy chicken", True, "🍗", False),
                ("Zinger Burger", 199.0, "Crispy chicken fillet with lettuce in sesame bun", True, "🍔", False),
                ("Popcorn Chicken (L)", 229.0, "Bite-sized tender crispy chicken popcorn", False, "🍿", False),
            ]),
            ("Smokin' Joe's", "Richmond Town", 4.2, 30, [
                ("Smoky BBQ Bacon Burger", 310.0, "Grilled patty with barbecue drizzle and grilled bacon", True, "🍔", False),
                ("Veggie Supreme Burger", 220.0, "Herb patty with grilled pineapple slice", True, "🍍", True),
            ]),
            ("Fatboy's Diner", "Kalyan Nagar", 4.5, 30, [
                ("Monster Triple Patty Burger", 450.0, "Three juicy smash patties with triple melted cheese", True, "🍔", False),
                ("Buffalo Wings with Blue Cheese", 270.0, "Tangy spicy buffalo wings served with celery sticks", False, "🍗", False),
            ]),
            ("Carl's Jr.", "Malleshwaram", 4.3, 25, [
                ("Famous Star Burger", 260.0, "Charbroiled patty with special sauce and pickles", True, "🍔", False),
                ("Hand-Breaded Chicken Tenders", 220.0, "Golden fried chicken breast strips with honey mustard", False, "🍗", False),
            ]),
        ]
    },
    {
        "cuisine": "North Indian & Mughlai",
        "emoji": "🍛",
        "restaurants": [
            ("The Great Indian Dhaba", "Old Airport Road", 4.7, 30, [
                ("Butter Chicken Special", 380.0, "Tender shredded tandoori chicken simmered in creamy makhani gravy", True, "🍲", False),
                ("Dal Makhani (Overnight Cooked)", 290.0, "Black lentils slow-simmered with butter and fresh cream", True, "🥣", True),
                ("Garlic Butter Naan (2 Pcs)", 110.0, "Clay oven baked flatbread brushed with fresh garlic butter", False, "🫓", True),
                ("Paneer Tikka Masala", 330.0, "Charcoal grilled paneer cubes in spiced tomato onion gravy", True, "🧀", True),
            ]),
            ("Punjab Grill", "UB City, Vittal Mallya Rd", 4.9, 35, [
                ("Murgh Makhani Royale", 460.0, "Rich tomato and cashew silk gravy with charbroiled chicken", True, "🍗", False),
                ("Amritsari Kulcha with Chole", 320.0, "Crispy potato stuffed kulcha with tangy Pindi chole", True, "🫓", True),
                ("Tandoori Tiger Prawns", 650.0, "Jumbo prawns marinated in ajwain and Kashmiri chillies", False, "🍤", False),
            ]),
            ("Haldiram's", "BTM Layout", 4.5, 20, [
                ("Special Chole Bhature (2 Pcs)", 190.0, "Fluffy bhaturas with spiced Punjabi chole, pickle and onions", True, "🫓", True),
                ("Raj Kachori Chaat", 140.0, "Crispy puffed shell filled with lentils, yogurt, chutneys", False, "🥗", True),
                ("Paneer Thali Deluxe", 299.0, "Complete meal with paneer, dal, rice, rotis and sweet", True, "🍱", True),
            ]),
            ("Karim's Old Delhi", "Shivajinagar", 4.6, 30, [
                ("Mutton Korma", 420.0, "Rich and aromatic gravy cooked in royal spices", True, "🍖", False),
                ("Chicken Jahangiri", 360.0, "Spicy chicken with caramelized onion and cashew paste", True, "🍗", False),
                ("Khamiri Roti (2 Pcs)", 80.0, "Traditional fermented soft Mughal bread", False, "🫓", True),
            ]),
            ("Moti Mahal Delux", "Jayanagar", 4.6, 35, [
                ("Original Butter Chicken (Since 1920)", 390.0, "The historic inventor recipe of butter chicken", True, "🍗", False),
                ("Paneer Lababdar", 320.0, "Soft paneer in chunky onion tomato cashew gravy", True, "🧀", True),
                ("Lacha Paratha (Butter)", 75.0, "Flaky multi-layered whole wheat bread", False, "🫓", True),
            ]),
            ("Dhaba 1986", "Marathahalli", 4.5, 30, [
                ("Dhaba Chicken Curry", 350.0, "Highway dhaba style rustic country chicken curry", True, "🍲", False),
                ("Pindi Chana Masala", 260.0, "Dry roasted spicy chickpeas cooked with anardana", True, "🍛", True),
                ("Tandoori Roti Basket", 140.0, "Assorted plain and butter tandoori rotis", False, "🫓", True),
            ]),
            ("Kake Da Hotel", "Koramangala", 4.4, 25, [
                ("Dahi Chicken", 340.0, "Thick spiced yogurt gravy chicken with whole spices", True, "🍗", False),
                ("Keema Kaleji", 380.0, "Minced mutton cooked with liver and green chillies", True, "🥘", False),
            ]),
            ("Sethi's Kitchen", "Whitefield", 4.3, 30, [
                ("Kadai Paneer", 290.0, "Cottage cheese tossed with bell peppers and crushed coriander", True, "🧀", True),
                ("Chicken Do Pyaza", 320.0, "Succulent chicken with double portions of sweet caramelized onions", True, "🍗", False),
            ]),
            ("Pind Balluchi", "Bannerghatta Road", 4.5, 35, [
                ("Murgh Malai Tikka", 330.0, "Boneless chicken marinated in cream, cheese and mild spices", False, "🍢", False),
                ("Dal Tadka Punjabi", 220.0, "Yellow lentils tempered with ghee, cumin and garlic", True, "🥣", True),
            ]),
            ("Chulha Chauki Da Dhaba", "JP Nagar", 4.6, 25, [
                ("Kulhad Lassi", 90.0, "Thick creamy sweet lassi served in traditional earthen cup", False, "🥛", True),
                ("Egg Curry Desi Style", 240.0, "Boiled eggs in homestyle spicy onion gravy", True, "🥚", False),
            ]),
        ]
    },
    {
        "cuisine": "South Indian & Coastal",
        "emoji": "🥞",
        "restaurants": [
            ("Dosa Diner", "Malleshwaram 8th Cross", 4.8, 20, [
                ("Mysore Masala Dosa", 130.0, "Crispy red chutney lined dosa filled with spiced potato palya", True, "🥞", True),
                ("Ghee Roast Podi Dosa", 150.0, "Golden dosa roasted in pure desi ghee with spicy gunpowder", True, "🥞", True),
                ("Medu Vada (2 Pcs) with Sambhar", 90.0, "Crispy fried lentil fritters with piping hot sambhar & coconut chutney", False, "🍩", True),
                ("Filter Coffee (Double Decoction)", 50.0, "Authentic South Indian chicory infused frothy filter coffee", False, "☕", True),
            ]),
            ("Murugan Idli Shop", "Commercial Street", 4.7, 20, [
                ("Ghee Podi Idli (4 Pcs)", 140.0, "Button idlis tossed in spicy molagapodi and clarified butter", True, "⚪", True),
                ("Onion Uttapam", 120.0, "Thick rice pancake topped with caramelized shallots", True, "🥞", True),
                ("Sweet Pongal", 90.0, "Jaggery and ghee cooked rice dessert with cashews", False, "🍯", True),
            ]),
            ("Vidyarthi Bhavan", "Gandhi Bazaar, Basavanagudi", 4.9, 25, [
                ("Heritage Masala Dosa", 110.0, "Legendary thick and crispy golden brown dosa with potato filling", True, "🥞", True),
                ("Rava Vada", 65.0, "Crisp semolina fritter with green chillies and curry leaves", False, "🍩", True),
                ("Kesari Bath", 60.0, "Saffron semolina halwa with pure ghee and pineapple", False, "🍮", True),
            ]),
            ("Saravana Bhavan", "MG Road", 4.5, 25, [
                ("Special South Indian Thali", 260.0, "Full vegetarian feast with 12 items including rasam, sambhar, kootu", True, "🍱", True),
                ("Rava Masala Dosa", 140.0, "Crisp semolina crepe stuffed with potato and cashew mix", True, "🥞", True),
                ("Curd Rice with Pomegranate", 110.0, "Comforting seasoned yogurt rice with mustard seeds", True, "🍚", True),
            ]),
            ("Kudla Coastal Kitchen", "Indiranagar", 4.7, 30, [
                ("Mangalorean Anjal (Kingfish) Rava Fry", 480.0, "Crispy semolina coated fresh kingfish steak", True, "🐟", False),
                ("Kori Rotti with Chicken Gassi", 360.0, "Crisp rice wafers soaked in spicy Mangalorean chicken coconut gravy", True, "🍛", False),
                ("Neer Dosa (4 Pcs)", 100.0, "Delicate paper-thin lace crepes", False, "🥞", True),
            ]),
            ("Anupam's Coast II Coast", "Church Street", 4.6, 35, [
                ("Silver Fish Rava Fry", 280.0, "Crunchy fried whitebait fish with lemon and onions", False, "🐟", False),
                ("Crab Ghee Roast", 580.0, "Fresh mud crab roasted in fiery Kundapur red masala and ghee", True, "🦀", False),
                ("Prawns Curry with Steamed Rice", 420.0, "Fresh prawns in tangy coastal coconut curry", True, "🍤", False),
            ]),
            ("Udupi Grand", "Koramangala", 4.4, 15, [
                ("Set Dosa with Sagu", 110.0, "Pancake stack of 3 soft sponge dosas with vegetable sagu", True, "🥞", True),
                ("Bisibelebath with Boondi", 120.0, "Spiced rice lentil khichdi cooked with vegetables and pure ghee", True, "🍲", True),
            ]),
            ("Taaza Thindi", "Jayanagar 4th T Block", 4.9, 15, [
                ("Chow Chow Bath", 90.0, "Classic sweet kesari bath paired with savoury khara bath", True, "🍛", True),
                ("Crispy Masala Dosa", 80.0, "Golden brown crisp dosa served with fresh coconut chutney", True, "🥞", True),
            ]),
            ("MTR 1924 (Mavalli Tiffin Room)", "Lalbagh Road", 4.8, 30, [
                ("Rava Idli (Inventor's Recipe)", 95.0, "Signature spiced semolina steamed cakes with potato sagu", True, "⚪", True),
                ("Chandrahara Sweet", 80.0, "Heritage fried pastry soaked in condensed milk cream", False, "🍮", True),
            ]),
            ("Coast to Coast Seafood", "Residency Road", 4.5, 30, [
                ("Squid Sukka", 340.0, "Fresh squid rings tossed in grated coconut and red chilli paste", False, "🦑", False),
                ("Fish Curry Rice Combo", 320.0, "Traditional coastal red fish curry with piping hot boiled rice", True, "🍛", False),
            ]),
        ]
    },
    {
        "cuisine": "Chinese & Pan-Asian",
        "emoji": "🥢",
        "restaurants": [
            ("Wok This Way", "Koramangala 6th Block", 4.7, 25, [
                ("Kung Pao Chicken", 340.0, "Stir-fried chicken with crunchy peanuts, dry red chillies, scallions", True, "🍗", False),
                ("Chilli Garlic Hakka Noodles", 240.0, "Wok-tossed noodles with shredded cabbage, bell peppers and burnt garlic", True, "🍜", True),
                ("Chicken Steamed Dimsums (6 Pcs)", 260.0, "Thin skinned dumplings served with spicy chilli dip", False, "🥟", False),
                ("Crispy Honey Chilli Potatoes", 210.0, "Crispy potato fries glazed in sesame honey and red chilli paste", False, "🥔", True),
            ]),
            ("Mainland China", "Church Street", 4.8, 35, [
                ("Crispy Lotus Stem with Sweet Chilli", 320.0, "Thin lotus root chips tossed in tangy sweet chilli glaze", False, "🥢", True),
                ("Diced Chicken in Szechuan Sauce", 390.0, "Spicy wok chicken with dried red peppers and ginger", True, "🍗", False),
                ("Yangchow Fried Rice", 340.0, "Delicate jasmine rice tossed with egg, chicken and prawns", True, "🍚", False),
            ]),
            ("Wow! Momo", "Garuda Mall", 4.4, 20, [
                ("Darjeeling Chicken Steam Momo (8 Pcs)", 189.0, "Classic minced chicken steamed dumplings", True, "🥟", False),
                ("Pan Fried Schezwan Veg Momo", 179.0, "Crisp pan-seared vegetable dumplings tossed in fiery schezwan sauce", True, "🥟", True),
                ("Momo Burger (Moburg)", 119.0, "Crispy fried momos sandwiched inside burger buns with spicy sauces", False, "🍔", True),
            ]),
            ("Berco's Chinese", "Indiranagar", 4.5, 30, [
                ("Thukpa Noodle Soup", 260.0, "Tibetan hot and comforting chicken broth noodle soup", True, "🍜", False),
                ("Manchurian Chicken Gravy", 330.0, "Classic Indo-Chinese chicken balls in dark soy garlic sauce", True, "🍲", False),
                ("Chilli Paneer Dry", 280.0, "Wok tossed paneer with green bell peppers and chillies", False, "🧀", True),
            ]),
            ("Tokyo Ramen & Bowls", "Lavelle Road", 4.8, 30, [
                ("Tonkotsu Style Rich Miso Ramen", 450.0, "Rich umami broth, springy noodles, soft-boiled ajitsuke egg, nori", True, "🍜", False),
                ("Tofu & Shiitake Ramen", 390.0, "Creamy sesame broth with grilled tofu and wild mushrooms", True, "🍜", True),
                ("Crispy Chicken Gyoza (5 Pcs)", 280.0, "Pan-seared Japanese dumplings with ponzu dipping sauce", False, "🥟", False),
            ]),
            ("Chung Wah", "Residency Road", 4.3, 25, [
                ("Dragon Chicken", 310.0, "Crisp chicken slivers tossed in cashew nuts and red spicy paste", False, "🍗", False),
                ("Egg Fried Rice & Chicken Gravy Combo", 299.0, "Satisfying single-person lunch bowl", True, "🍚", False),
            ]),
            ("Noodle Nexus", "HSR Layout", 4.4, 25, [
                ("Pad Thai Noodles", 340.0, "Flat rice noodles with tamarind, crushed peanuts, sprouts and tofu", True, "🍜", True),
                ("Tom Yum Soup Chicken", 230.0, "Aromatic spicy sour soup with lemongrass, galangal and lime", False, "🥣", False),
            ]),
            ("Dimsum Stop", "Brigade Road", 4.5, 20, [
                ("Truffle Edamame Dumplings", 360.0, "Crystal skin dumplings filled with pureed edamame and truffle essence", True, "🥟", True),
                ("Spicy Prawn Har Gow", 390.0, "Juicy whole shrimp steamed inside translucent tapioca skin", True, "🥟", False),
            ]),
            ("Beijing Bites", "JP Nagar", 4.2, 30, [
                ("Golden Fried Prawns", 380.0, "Crispy crumb coated prawns served with sweet and sour sauce", False, "🍤", False),
                ("Veg American Chopsuey", 270.0, "Crispy fried noodles topped with sweet and tangy vegetable sauce", True, "🍝", True),
            ]),
            ("Siam Thai Kitchen", "Ulsoor", 4.7, 35, [
                ("Thai Green Chicken Curry with Jasmine Rice", 420.0, "Fragrant coconut curry with pea aubergines and basil", True, "🍛", False),
                ("Raw Papaya Salad (Som Tum)", 240.0, "Crunchy shredded green papaya with bird's eye chillies and peanuts", False, "🥗", True),
            ]),
        ]
    },
    {
        "cuisine": "Healthy, Salads & Bowls",
        "emoji": "🥗",
        "restaurants": [
            ("Vegan Delights", "Indiranagar", 4.7, 25, [
                ("Avocado & Quinoa Power Bowl", 340.0, "Fresh Hass avocado, organic quinoa, edamame, lemon tahini dressing", True, "🥑", True),
                ("Tofu Teriyaki Buddha Bowl", 310.0, "Charred tofu, brown rice, broccoli, purple cabbage, sesame seeds", True, "🥗", True),
                ("Green Detox Cold-Pressed Juice", 150.0, "Spinach, celery, cucumber, green apple, ginger", False, "🧃", True),
            ]),
            ("Subway", "Koramangala Sony Signal", 4.4, 20, [
                ("Roasted Chicken Sub (6 Inch)", 249.0, "Tender roasted chicken strips with choice of fresh veggies and sauces", True, "🥪", False),
                ("Paneer Tikka Sub (6 Inch)", 219.0, "Spiced paneer cubes with mint mayo and crunchy vegetables", True, "🥪", True),
                ("Double Chocolate Chip Cookie", 55.0, "Fresh baked chewy double chocolate cookie", False, "🍪", True),
            ]),
            ("The Salad Bar", "MG Road", 4.5, 25, [
                ("Caesar Chicken Salad", 290.0, "Romaine lettuce, grilled chicken breast, herb croutons, shaved parmesan", True, "🥗", False),
                ("Greek Feta & Olive Salad", 260.0, "Cucumbers, cherry tomatoes, kalamata olives, bell peppers and Greek feta", True, "🧀", True),
                ("Berry Chia Seed Pudding", 160.0, "Almond milk chia pudding topped with blueberries and honey", False, "🫐", True),
            ]),
            ("FreshMenu", "Domlur", 4.3, 25, [
                ("Burrito Bowl Grilled Chicken", 299.0, "Mexican rice, black beans, fajita chicken, salsa and sour cream", True, "🍲", False),
                ("Mediterranean Mezze Platter", 269.0, "Hummus, falafel, pita bread and pickled veggies", True, "🧆", True),
                ("Grilled Fish with Lemon Butter Rice", 360.0, "Pan-seared basa fillet with garlic butter rice and sautéed veggies", True, "🐟", False),
            ]),
            ("EatFit", "HSR Layout", 4.6, 20, [
                ("Dal Khichdi & Fruit Bowl", 199.0, "Homestyle comfort khichdi with roasted papad and fresh cut fruits", True, "🍲", True),
                ("Butter Chicken Khichdi Bowl", 249.0, "Guilt-free high-protein brown rice khichdi with butter chicken flavours", True, "🍛", False),
                ("Cult Fit High Protein Smoothie", 170.0, "Whey protein, banana, peanut butter and almond milk", False, "🥤", True),
            ]),
            ("Habit Healthy Eatery", "Koramangala", 4.6, 30, [
                ("Falafel Wrap with Hummus", 220.0, "Crispy baked chickpea falafel in multigrain wrap", True, "🌯", True),
                ("Grilled Salmon Salad", 520.0, "Pan-seared Atlantic salmon with mixed field greens", True, "🐟", False),
            ]),
            ("Keto Culture", "Indiranagar", 4.5, 30, [
                ("Almond Flour Keto Pizza", 390.0, "Zero carb almond crust with mozzarella and pepperoni", True, "🍕", False),
                ("Keto Butter Coffee", 140.0, "Black coffee blended with MCT oil and unsalted grass-fed butter", False, "☕", True),
            ]),
            ("Protein Station", "Whitefield", 4.4, 25, [
                ("Grilled Chicken Breast with Steamed Veggies", 310.0, "300g seasoned chicken breast with broccoli and beans", True, "🍗", False),
                ("Boiled Egg White Salad", 160.0, "6 boiled egg whites tossed with lime, pepper and greens", True, "🥚", False),
            ]),
            ("NutriBowl Co.", "Bellandur", 4.5, 20, [
                ("Smoked Tofu Poke Bowl", 320.0, "Japanese sushi rice, edamame, pickled cucumber, sesame ginger sauce", True, "🍚", True),
                ("Açai Berry Superbowl", 280.0, "Blended organic açai topped with granola and fresh fruits", False, "🍓", True),
            ]),
            ("The Green Kitchen", "Jayanagar", 4.3, 25, [
                ("Millet Bisi Bele Bath", 170.0, "Foxtail millet cooked with vegetables and spices", True, "🍲", True),
                ("Sprouted Moong Salad", 130.0, "Sprouted lentils with onions, tomatoes and chaat masala", False, "🥗", True),
            ]),
        ]
    },
    {
        "cuisine": "Desserts, Bakery & Cafes",
        "emoji": "🍰",
        "restaurants": [
            ("Theobroma", "Koramangala 4th Block", 4.8, 25, [
                ("Overload Brownie", 125.0, "Dense chocolate brownie overloaded with melted chocolate chunks", True, "🍫", True),
                ("Millionaire Brownie", 135.0, "Layers of dark chocolate, sea salt caramel and butter shortbread", True, "🍫", True),
                ("Red Velvet Pastry", 150.0, "Classic red velvet sponge with rich cream cheese frosting", False, "🍰", True),
                ("Nutella Hazelnut Tart", 160.0, "Crisp pastry shell filled with pure Nutella and roasted hazelnuts", False, "🥧", True),
            ]),
            ("The Belgian Waffle Co.", "HSR Layout", 4.7, 20, [
                ("Naked Nutella Waffle", 170.0, "Fresh baked crispy warm waffle loaded with pure Nutella", True, "🧇", True),
                ("Triple Chocolate Waffle", 160.0, "Dark chocolate waffle with milk, white and dark chocolate drizzles", True, "🧇", True),
                ("Lotus Biscoff Waffle", 185.0, "Waffle topped with crunchy caramelised Biscoff spread and biscuit crumbs", True, "🧇", True),
            ]),
            ("Starbucks", "Indiranagar 100ft Rd", 4.6, 25, [
                ("Caffe Latte (Grande)", 290.0, "Rich espresso balanced with steamed milk and light layer of foam", False, "☕", True),
                ("Java Chip Frappuccino", 370.0, "Mocha sauce and Frappuccino chips blended with milk and ice", False, "🥤", True),
                ("Butter Croissant", 195.0, "Flaky multi-layered golden all-butter French croissant", False, "🥐", True),
                ("Smoked Chicken Sandwich", 280.0, "Smoked chicken breast with honey mustard in grilled panini", True, "🥪", False),
            ]),
            ("Naturals Ice Cream", "Jayanagar", 4.9, 20, [
                ("Tender Coconut Ice Cream (200ml)", 110.0, "Real tender coconut pulp in creamy rich milk base", True, "🥥", True),
                ("Sitaphal (Custard Apple) Ice Cream", 120.0, "Fresh custard apple pulp hand-crafted seasonal ice cream", True, "🍦", True),
                ("Roasted Almond Ice Cream", 120.0, "Crunchy roasted Californian almonds in velvety ice cream", False, "🍨", True),
            ]),
            ("Glen's Bakehouse", "Lavelle Road", 4.8, 25, [
                ("Mini Red Velvet Cupcakes (Set of 6)", 210.0, "Famous bite-sized moist red velvet cupcakes with cream cheese", True, "🧁", True),
                ("Almond Croissant", 180.0, "Butter croissant filled with almond frangipane cream", False, "🥐", True),
                ("Chicken Pot Pie", 190.0, "Flaky puff pastry stuffed with creamy chicken and vegetables", True, "🥧", False),
            ]),
            ("Chai Point", "Embassy TechVillage", 4.4, 15, [
                ("Ginger Cardamom Chai Flask (500ml)", 160.0, "Serves 3-4 cups of piping hot milk tea in insulated flask", False, "☕", True),
                ("Bun Maska with Jam", 85.0, "Soft bun slit and generously buttered with fruit jam", False, "🍞", True),
                ("Egg Puff (2 Pcs)", 90.0, "Crispy puff pastry with spiced hard-boiled egg inside", False, "🥐", False),
            ]),
            ("Corner House Ice Cream", "Residency Road", 4.9, 25, [
                ("Death By Chocolate (DBC)", 260.0, "Iconic layered cake, rich vanilla ice cream, hot chocolate fudge and peanuts", True, "🍨", True),
                ("Trilogy", 220.0, "Combination of vanilla, strawberry and chocolate with fruit toppings", False, "🍧", True),
            ]),
            ("Magnolia Bakery", "Indiranagar", 4.7, 30, [
                ("Famous Banana Pudding (Classic)", 260.0, "Layers of vanilla wafers, fresh bananas and creamy vanilla pudding", True, "🍌", True),
                ("Carrot Cake with Cream Cheese", 280.0, "Moist spiced carrot cake studded with walnuts", False, "🍰", True),
            ]),
            ("Smoor Chocolates & Cafe", "Indiranagar", 4.6, 25, [
                ("Hot Chocolate Deluxe", 220.0, "Thick melted Belgian chocolate drink", False, "☕", True),
                ("Dark Chocolate Truffle Cake (Pastry)", 240.0, "70% dark chocolate ganache layered with chocolate sponge", True, "🎂", True),
            ]),
            ("Third Wave Coffee", "Koramangala 4th Block", 4.7, 20, [
                ("Classic Cold Brew", 210.0, "18-hour slow steeped specialty Arabica coffee over ice", False, "🧊", True),
                ("Avocado Toast on Sourdough", 270.0, "Crushed avocado with chili flakes and microgreens", True, "🥑", True),
            ]),
        ]
    },
    {
        "cuisine": "Street Food & Snacks",
        "emoji": "🥟",
        "restaurants": [
            ("Spicy Corner", "VV Puram Food Street", 4.7, 20, [
                ("Pani Puri (6 Pcs with 2 Waters)", 70.0, "Crispy puris with spicy mint water and sweet tamarind chutney", True, "🥟", True),
                ("Sev Puri Special", 90.0, "Crispy flat puris topped with potatoes, onions, chutneys and nylon sev", True, "🥙", True),
                ("Dahi Papdi Chaat", 110.0, "Crunchy papdis bathed in sweetened yogurt, roasted cumin and pomegranate", True, "🥗", True),
                ("Samosa Pav (2 Pcs)", 80.0, "Hot spiced potato samosas pressed inside buttered pav with spicy garlic chutney", False, "🥪", True),
            ]),
            ("Tibetan Mother's Kitchen", "Koramangala", 4.6, 25, [
                ("Chicken Kothey Momo (Pan-fried 8 Pcs)", 190.0, "Crispy bottom pan-fried momos with fiery red sesame paste", True, "🥟", False),
                ("Thukpa Vegetable Noodle Broth", 160.0, "Hearty mountain vegetable noodle soup", True, "🍜", True),
                ("Chicken Shapta", 240.0, "Stir-fried sliced chicken with onions, capsicum and ginger", False, "🍗", False),
            ]),
            ("Falahaar - Pure Satvik & Vrat", "BTM Layout", 4.5, 20, [
                ("Sabudana Khichdi with Curd", 140.0, "Sago pearls sautéed with roasted crushed peanuts, green chillies and cumin", True, "🍲", True),
                ("Sabudana Vada (2 Pcs)", 110.0, "Crisp golden fried sago and potato patties", False, "🍩", True),
            ]),
            ("Goli Vada Pav", "Malleshwaram", 4.3, 15, [
                ("Classic Vada Pav (2 Pcs)", 80.0, "Deep fried potato dumpling in pav with dry garlic coconut chutney", True, "🍔", True),
                ("Cheese Corn Vada Pav", 95.0, "Melted cheese and sweet corn stuffed inside crisp potato patty", True, "🧀", True),
            ]),
            ("Anand Sweets & Purveyors", "Commercial Street", 4.8, 25, [
                ("Kaju Katli (250g)", 290.0, "Diamond shaped pure cashew fudge topped with silver vark", False, "🍬", True),
                ("Motichoor Laddu (250g)", 190.0, "Fine besan boondi laddus cooked in pure desi ghee", False, "🟡", True),
                ("Samosa with Mint Chutney (2 Pcs)", 60.0, "Crisp Punjabi samosas with spicy potato and green pea stuffing", False, "🥟", True),
            ]),
            ("Kathi Junction", "HSR Layout", 4.4, 20, [
                ("Double Egg Chicken Roll", 170.0, "Paratha layered with double eggs, grilled chicken and lemon onions", True, "🌯", False),
                ("Paneer Tikka Roll", 150.0, "Spiced paneer cubes wrapped in layered paratha with mint sauce", True, "🌯", True),
            ]),
            ("Al-Amanah Cafe", "Kammanahalli", 4.7, 30, [
                ("Kuboos Chicken Jumbo Roll", 220.0, "Oversized Arabian roll stuffed with french fries, mayo and chicken", True, "🌯", False),
                ("Beef / Mutton Spicy Roll", 240.0, "Juicy seasoned meat chunks in soft flatbread", True, "🌯", False),
            ]),
            ("Rolls & Bowls", "Bellandur", 4.3, 20, [
                ("Mutton Seekh Kebab Roll", 210.0, "Charcoal grilled spiced mutton seekh wrapped in flaky rumali", True, "🌯", False),
                ("Veggie Corn Roll", 120.0, "Sweet corn and mixed vegetable filling with chipotle mayo", False, "🌯", True),
            ]),
            ("Kota Kachori", "Koramangala 7th Block", 4.6, 20, [
                ("Pyaaz Kachori (2 Pcs) with Kadhi", 110.0, "Rajasthan special flaky onion stuffed kachoris served with spicy kadhi", True, "🥟", True),
                ("Jalebi (200g Desi Ghee)", 120.0, "Piping hot crispy spirals soaked in saffron cardamom sugar syrup", False, "🥨", True),
            ]),
            ("Bombay Chowpatty", "Indiranagar", 4.4, 20, [
                ("Pav Bhaji Extra Butter (2 Pavs)", 160.0, "Mashed vegetable curry topped with molten Amul butter and onions", True, "🥘", True),
                ("Bhel Puri Bombay Style", 80.0, "Puffed rice tossed with potatoes, sev and sweet spicy chutneys", False, "🥗", True),
            ]),
        ]
    }
]

def seed_100_restaurants():
    """Populates 100 realistic restaurants with menus into SQLite."""
    create_tables()
    db = SessionLocal()
    try:
        # Check current count
        count = db.query(Restaurant).count()
        if count >= 80:
            print(f"ℹ️ Database already has {count} restaurants. Skipping 100 restaurants seed.")
            return

        print("🚀 Seeding 100 realistic restaurants with rich menus...")
        created_count = 0
        menu_items_count = 0

        for cat in CATEGORIES:
            cuisine_name = cat["cuisine"]
            for rest_data in cat["restaurants"]:
                name, address, rating, delivery_min, dishes = rest_data
                rest_id = f"REST-{uuid.uuid4().hex[:8].upper()}"

                restaurant = Restaurant(
                    id=rest_id,
                    name=name,
                    cuisine_type=cuisine_name,
                    address=address,
                    phone=f"+91 {random.randint(90000, 99999)} {random.randint(10000, 99999)}",
                    rating=rating,
                    is_active=True,
                    delivery_time_min=delivery_min,
                    min_order_amount=100.0,
                )
                db.add(restaurant)
                created_count += 1

                for dish in dishes:
                    d_name, d_price, d_desc, is_main, emoji, is_veg = dish
                    m_item = MenuItem(
                        id=f"ITEM-{uuid.uuid4().hex[:8].upper()}",
                        restaurant_id=rest_id,
                        name=d_name,
                        price=d_price,
                        description=d_desc,
                        category=cuisine_name,
                        is_veg=is_veg,
                        rating=round(rating - random.uniform(0.0, 0.3), 1),
                        image_emoji=emoji,
                    )
                    db.add(m_item)
                    menu_items_count += 1

        db.commit()
        print(f"✅ Successfully seeded {created_count} restaurants with {menu_items_count} signature menu dishes!")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding restaurants: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_100_restaurants()
