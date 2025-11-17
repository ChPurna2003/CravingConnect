from models import db, User, Restaurant, MenuItem, PaymentMethod
from app import create_app
import os

def seed():
    app = create_app()
    with app.app_context():
        # reset DB
        db.drop_all()
        db.create_all()

        # Users (seed passwords: 'password')
        users = [
            ("nick", "password", "admin", None),
            ("captain_marvel", "password", "manager", "India"),
            ("captain_america", "password", "manager", "America"),
            ("thanos", "password", "member", "India"),
            ("thor", "password", "member", "India"),
            ("travis", "password", "member", "America"),
        ]
        for username, pwd, role, country in users:
            u = User(username=username, role=role, country=country)
            u.set_password(pwd)
            db.session.add(u)
        db.session.commit()

        # Restaurants
        r1 = Restaurant(name="Spice India", country="India")
        r2 = Restaurant(name="Yankee Diner", country="America")
        r3 = Restaurant(name="Burger Place", country="America")
        r4 = Restaurant(name="Pizza Heaven", country="India")

        db.session.add_all([r1, r2, r3, r4])
        db.session.commit()

        # Menu Items
        items = [
            MenuItem(restaurant_id=r1.id, name="Butter Chicken", price=8.50),
            MenuItem(restaurant_id=r1.id, name="Naan", price=1.50),

            MenuItem(restaurant_id=r2.id, name="Burger", price=6.00),
            MenuItem(restaurant_id=r2.id, name="Fries", price=2.00),

            MenuItem(restaurant_id=r3.id, name="Cheeseburger", price=7.99),
            MenuItem(restaurant_id=r3.id, name="Fries", price=2.99),
            MenuItem(restaurant_id=r3.id, name="Chicken Wrap", price=6.49),

            MenuItem(restaurant_id=r4.id, name="Pepperoni Pizza", price=9.49),
            MenuItem(restaurant_id=r4.id, name="Margherita Pizza", price=8.79),
            MenuItem(restaurant_id=r4.id, name="Garlic Bread", price=3.49),
        ]
        db.session.add_all(items)
        db.session.commit()

        # Payment methods for admin
        admin = User.query.filter_by(username="nick").first()
        pm = PaymentMethod(
            user_id=admin.id,
            card_last4="1111",
            method_name="Admin Card"
        )
        db.session.add(pm)
        db.session.commit()

        print("Seeded DB.")

if __name__ == "__main__":
    seed()
