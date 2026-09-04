import os
from app import app
from models import db, Category, Product, Inquiry, Order, OrderItem, AdminUser

def seed_database():
    with app.app_context():
        # Drop and re-create tables for clean setup
        db.drop_all()
        db.create_all()
        
        print("[+] Seeding database for Gifric Farm...")

        # Default Admin User
        admin_user = AdminUser(username="admin", email="progressezekiel00@gmail.com")
        admin_user.set_password("gifricadmin2026")
        db.session.add(admin_user)
        db.session.commit()

        # Categories
        cat_veg = Category(
            name="Fresh Vegetables & Greens", 
            slug="fresh-vegetables-greens", 
            description="Organically grown spinach, crisp cabbages, field tomatoes, and leafy greens harvested fresh daily."
        )
        cat_mushrooms = Category(
            name="Gourmet Mushrooms", 
            slug="gourmet-mushrooms", 
            description="Crisp white button mushrooms and tender oyster mushrooms grown under strict climate control."
        )
        cat_chicken = Category(
            name="Fresh Whole Chicken", 
            slug="fresh-whole-chicken", 
            description="Farm fresh, organically raised whole broilers and layers ($7 per bird) processed under strict hygiene."
        )
        cat_cuts = Category(
            name="Chicken Cuts & Parts", 
            slug="chicken-cuts-parts", 
            description="Prime cut chicken breast, wings, and drumsticks cleaned, trimmed, and blast chilled."
        )
        cat_eggs = Category(
            name="Farm Fresh Eggs", 
            slug="farm-fresh-eggs", 
            description="Nutrient-dense, golden yolk eggs gathered daily from our free-range hens."
        )
        cat_feed = Category(
            name="Poultry Feed & Farm Supplies", 
            slug="poultry-feed-farm-supplies", 
            description="Nutritiously balanced organic poultry starter feeds, grains, and farm supplies."
        )

        db.session.add_all([cat_veg, cat_mushrooms, cat_chicken, cat_cuts, cat_eggs, cat_feed])
        db.session.commit()

        # Products
        products = [
            # Gourmet Mushrooms
            Product(
                category_id=cat_mushrooms.id,
                name="Farm Fresh White Button Mushrooms (250g Punnet)",
                slug="fresh-white-button-mushrooms-250g",
                price=2.50,
                unit="per 250g punnet",
                description="Crisp, earthy, freshly picked white button mushrooms. Perfect for sautés, cream soups, pizzas, and vegetable stir-fries. Hand-picked at peak maturity.",
                short_description="Freshly picked tender white button mushrooms in a sealed 250g punnet.",
                image_url="https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=800&q=80",
                stock_quantity=150,
                is_featured=True,
                is_organic=True,
                is_halal=True
            ),
            Product(
                category_id=cat_mushrooms.id,
                name="Organic Grey Oyster Mushrooms (Fresh Harvest)",
                slug="organic-grey-oyster-mushrooms",
                price=3.00,
                unit="per 250g punnet",
                description="Delicate, velvety oyster mushrooms with a mild savory flavor. Grown on organic sterilized agricultural substrate, chemical-free.",
                short_description="Velvety organic oyster mushrooms with rich umami flavor.",
                image_url="https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80",
                stock_quantity=100,
                is_featured=True,
                is_organic=True,
                is_halal=True
            ),

            # Fresh Vegetables & Greens
            Product(
                category_id=cat_veg.id,
                name="Farm Fresh Organic Spinach Bundle",
                slug="farm-fresh-organic-spinach-bundle",
                price=1.00,
                unit="per bundle",
                description="Lush, tender green organic spinach leaves hand-cut early morning. Rich in iron, vitamins, and minerals. Washed and tied in generous bundles.",
                short_description="Freshly cut garden spinach bundle with deep green leaves.",
                image_url="https://images.unsplash.com/photo-1576045057995-568f588f82fb?auto=format&fit=crop&w=800&q=80",
                stock_quantity=200,
                is_featured=True,
                is_organic=True,
                is_halal=True
            ),
            Product(
                category_id=cat_veg.id,
                name="Ripe Red Roma Field Tomatoes (10kg Wooden Crate)",
                slug="ripe-red-roma-tomatoes-crate",
                price=9.50,
                unit="per crate",
                description="Firm, meaty, sun-ripened Roma field tomatoes. Excellent for rich relishes, tomato sauces, and salads. Packaged in a sturdy 10kg farm crate.",
                short_description="Sweet sun-ripened 10kg farm crate of firm Roma tomatoes.",
                image_url="https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=800&q=80",
                stock_quantity=80,
                is_featured=True,
                is_organic=True,
                is_halal=True
            ),
            Product(
                category_id=cat_veg.id,
                name="Crisp Green Sugarloaf Cabbage",
                slug="crisp-green-sugarloaf-cabbage",
                price=1.20,
                unit="per head",
                description="Dense, sweet, crunchy green cabbage head grown in fertile soils. Great for coleslaws, vegetable sautés, and traditional braises.",
                short_description="Solid, crunchy whole green cabbage head.",
                image_url="https://images.unsplash.com/photo-1594282486552-05b4d80fbb9f?auto=format&fit=crop&w=800&q=80",
                stock_quantity=180,
                is_featured=False,
                is_organic=True,
                is_halal=True
            ),

            # Fresh Whole Chicken ($7 per bird)
            Product(
                category_id=cat_chicken.id,
                name="Gifric Premium Whole Broiler Chicken (2.0kg - 2.5kg)",
                slug="gifric-premium-whole-broiler",
                price=7.00,
                unit="per bird",
                description="Tender, farm-reared organic broiler chicken raised on natural grain feeds. Dressed, thoroughly cleaned, and blast-chilled for peak freshness ($7/bird).",
                short_description="Farm fresh, tender whole dressed broiler chicken ($7 per bird).",
                image_url="https://images.unsplash.com/photo-1587593810167-a84920ea0781?auto=format&fit=crop&w=800&q=80",
                stock_quantity=200,
                is_featured=True,
                is_organic=True,
                is_halal=True
            ),
            Product(
                category_id=cat_chicken.id,
                name="Free-Range Organic Heritage Layer Hen",
                slug="free-range-heritage-layer-hen",
                price=7.00,
                unit="per bird",
                description="Traditional free-range mature hen known for deep flavorful meat, ideal for stews, soups, and slow-roasted dishes ($7/bird).",
                short_description="Rich-flavored mature free-range hen ($7 per bird).",
                image_url="https://images.unsplash.com/photo-1548550023-2bdb3c5beed7?auto=format&fit=crop&w=800&q=80",
                stock_quantity=120,
                is_featured=False,
                is_organic=True,
                is_halal=True
            ),
            
            # Chicken Cuts & Parts
            Product(
                category_id=cat_cuts.id,
                name="Skinless Boneless Chicken Breast Fillet (1kg)",
                slug="skinless-boneless-chicken-breast-1kg",
                price=6.50,
                unit="per kg",
                description="Lean, high-protein chicken breast cutlets, hand-trimmed and skinless. Ideal for grilling, meal prepping, and stir-fries.",
                short_description="Lean, hand-trimmed 100% pure chicken breast meat.",
                image_url="https://images.unsplash.com/photo-1604503468506-a8da13d82791?auto=format&fit=crop&w=800&q=80",
                stock_quantity=200,
                is_featured=True,
                is_organic=True,
                is_halal=True
            ),
            Product(
                category_id=cat_cuts.id,
                name="Jumbo Fresh Chicken Wings (Party Pack 2kg)",
                slug="jumbo-fresh-chicken-wings-2kg",
                price=9.50,
                unit="per 2kg pack",
                description="Meaty, juicy split wings (flats & drumettes). Perfect for BBQ, baking, or crispy frying.",
                short_description="Fresh 2kg party pack of plump split chicken wings.",
                image_url="https://images.unsplash.com/photo-1527477396000-e27163b481c2?auto=format&fit=crop&w=800&q=80",
                stock_quantity=120,
                is_featured=True,
                is_organic=True,
                is_halal=True
            ),

            # Farm Fresh Eggs
            Product(
                category_id=cat_eggs.id,
                name="Gifric Golden Yolk Organic Brown Eggs (Tray of 30)",
                slug="gifric-brown-eggs-tray-30",
                price=5.00,
                unit="per tray of 30",
                description="Large, thick-shelled brown eggs with deep orange rich yolks. Laid daily by pasture-raised hens fed organic grains.",
                short_description="Fresh brown eggs tray with golden rich yolks.",
                image_url="https://images.unsplash.com/photo-1516467508483-a7212febe31a?auto=format&fit=crop&w=800&q=80",
                stock_quantity=300,
                is_featured=True,
                is_organic=True,
                is_halal=True
            ),

            # Feed & Supplies
            Product(
                category_id=cat_feed.id,
                name="Gifric Bio-Grow Organic Broiler Starter Crumble (50kg Bag)",
                slug="gifric-broiler-starter-crumble-50kg",
                price=22.50,
                unit="per 50kg bag",
                description="High-protein (22% crude protein) balanced starter feed formulated with amino acids and essential vitamins.",
                short_description="50kg premium high-protein organic chick starter feed.",
                image_url="https://images.unsplash.com/photo-1500595046743-cd271d694d30?auto=format&fit=crop&w=800&q=80",
                stock_quantity=100,
                is_featured=False,
                is_organic=True,
                is_halal=True
            )
        ]

        db.session.add_all(products)
        db.session.commit()

        # Seed sample initial inquiry
        sample_inquiry = Inquiry(
            name="Tinashe Moyo",
            email="tinashe.moyo@hararekitchen.co.zw",
            phone="+263 77 123 4567",
            service_type="wholesale",
            subject="Weekly Vegetables, Mushrooms & Whole Chicken Bulk Delivery",
            message="Hi Gifric Farm team! We run a restaurant in Hatfield, Harare and would like weekly deliveries of 20kg fresh button mushrooms, 30 bundles of spinach, and 40 whole chickens at $7 per bird. Please advise.",
            status="Unread"
        )
        db.session.add(sample_inquiry)

        # Seed sample initial order
        sample_order = Order(
            order_number="GF-2026-8801",
            customer_name="Blessing Chikore",
            email="b.chikore@example.co.zw",
            phone="+263 77 223 9953",
            delivery_address="84 St Andrews Rd, Hatfield",
            city="Harare",
            payment_method="cash",
            status="Confirmed",
            total_amount=24.00,
            notes="Please deliver fresh vegetables and chicken before 11 AM."
        )
        db.session.add(sample_order)
        db.session.commit()

        item1 = OrderItem(
            order_id=sample_order.id,
            product_id=products[0].id, # Button Mushrooms
            product_name=products[0].name,
            price=products[0].price, # $2.50
            quantity=2,
            subtotal=5.00
        )
        item2 = OrderItem(
            order_id=sample_order.id,
            product_id=products[5].id, # Whole Chicken
            product_name=products[5].name,
            price=products[5].price, # $7.00
            quantity=2,
            subtotal=14.00
        )
        item3 = OrderItem(
            order_id=sample_order.id,
            product_id=products[9].id, # Brown Eggs tray
            product_name=products[9].name,
            price=products[9].price, # $5.00
            quantity=1,
            subtotal=5.00
        )
        db.session.add_all([item1, item2, item3])
        db.session.commit()

        print("[SUCCESS] Database successfully re-seeded for Gifric Farm (Agricultural Produce: Vegetables, Mushrooms, Poultry, Eggs)!")

if __name__ == "__main__":
    seed_database()
