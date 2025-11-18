# backend/db_init.py
from backend.models import db, User, Restaurant, MenuItem, PaymentMethod

def seed_data():
    # If users already exist → skip seeding
    if User.query.first():
        return

    # ---- USERS ----
    users = [
        ("nick", "admin", "India"),
        ("captain_marvel", "manager", "India"),
        ("captain_america", "manager", "America"),
        ("thanos", "member", "India"),
        ("thor", "member", "India"),
        ("travis", "member", "America")
    ]

    created_users = []

    for username, role, country in users:
        u = User(username=username, role=role, country=country)
        u.set_password("password")
        db.session.add(u)
        created_users.append(u)

    db.session.commit()

    # ---- RESTAURANTS ----
    r1 = Restaurant(name="Spice India", country="India")
    r2 = Restaurant(name="Biryani House", country="India")
    r3 = Restaurant(name="Burger Point", country="America")
    r4 = Restaurant(name="Pizza Hub", country="America")

    db.session.add_all([r1, r2, r3, r4])
    db.session.commit()

    # ---- MENU ----
    items = [
        MenuItem(restaurant_id=r1.id, name="Butter Chicken", price=100.00),
        MenuItem(restaurant_id=r1.id, name="Naan", price=15.00),
        MenuItem(restaurant_id=r2.id, name="Veg Biryani", price=150.00),
        MenuItem(restaurant_id=r2.id, name="Chicken Biryani", price=180.00),
        MenuItem(restaurant_id=r3.id, name="Burger", price=6.49),
        MenuItem(restaurant_id=r3.id, name="Fries", price=2.99),
        MenuItem(restaurant_id=r4.id, name="Pepperoni Pizza", price=9.49),
        MenuItem(restaurant_id=r4.id, name="Margherita Pizza", price=8.79)
    ]

    db.session.add_all(items)
    db.session.commit()

    # ---- ADMIN PAYMENT ----
    admin = User.query.filter_by(username="nick").first()
    pm = PaymentMethod(user_id=admin.id, method_name="Admin Card", card_last4="1111")

    db.session.add(pm)
    db.session.commit()

    print("Database created & seeded.")
