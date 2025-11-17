# backend/models.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()


# ------------------------------------------------------------
# USER MODEL
# ------------------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # Role: admin / manager / member
    role = db.Column(db.String(20), nullable=False)

    # Country (India / America)
    country = db.Column(db.String(50), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, pwd):
        return check_password_hash(self.password_hash, pwd)

    def is_admin(self):
        return self.role == "admin"

    def is_manager(self):
        return self.role == "manager"

    def is_member(self):
        return self.role == "member"



# ------------------------------------------------------------
# RESTAURANTS
# ------------------------------------------------------------
class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

    # Country of restaurant (India / America)
    country = db.Column(db.String(50), nullable=False)

    menu_items = db.relationship(
        'MenuItem', 
        backref='restaurant',
        cascade="all,delete"
    )



# ------------------------------------------------------------
# MENU ITEMS
# ------------------------------------------------------------
class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    restaurant_id = db.Column(
        db.Integer, 
        db.ForeignKey('restaurant.id'), 
        nullable=False
    )

    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)



# ------------------------------------------------------------
# PAYMENT METHODS
# ------------------------------------------------------------
class PaymentMethod(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('user.id'), 
        nullable=False
    )

    card_last4 = db.Column(db.String(4), nullable=False)
    method_name = db.Column(db.String(80), nullable=False)

    user = db.relationship('User', backref='payment_methods')



# ------------------------------------------------------------
# ORDER MODEL
# ------------------------------------------------------------
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('user.id'), 
        nullable=False
    )

    restaurant_id = db.Column(
        db.Integer, 
        db.ForeignKey('restaurant.id'), 
        nullable=False
    )

    status = db.Column(db.String(30), default="cart")  
    # cart / placed / cancelled

    total = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ⭐ FIX ADDED: REQUIRED FOR YOUR APP
    country = db.Column(db.String(50), nullable=True)
    # Used for:
    # - Currency mapping
    # - Manager/Member country restriction
    # - Order filtering

    # relationships
    items = db.relationship('OrderItem', backref='order', cascade="all,delete")
    user = db.relationship('User')
    restaurant = db.relationship('Restaurant')

    added_by = db.Column(db.String(50))
    cancelled_by = db.Column(db.String(50))



# ------------------------------------------------------------
# ORDER ITEMS
# ------------------------------------------------------------
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer, 
        db.ForeignKey('order.id'), 
        nullable=False
    )

    menu_item_id = db.Column(
        db.Integer, 
        db.ForeignKey('menu_item.id'),
        nullable=False
    )

    qty = db.Column(db.Integer, default=1)

    menu_item = db.relationship('MenuItem')
