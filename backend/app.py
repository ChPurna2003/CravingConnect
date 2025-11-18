# backend/app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from backend.models import db, User, Restaurant, MenuItem, PaymentMethod, Order, OrderItem
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os


def create_app():
    app = Flask(
        __name__,
        template_folder="../frontend/templates",
        static_folder="../frontend/static"
    )

    # Database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foodapp.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Secret key (Render will set env variable)
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-secret")

    db.init_app(app)

    # ----------------------------------------------------
    # LOGIN MANAGER
    # ----------------------------------------------------
    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(uid):
        return User.query.get(int(uid))

    # ----------------------------------------------------
    # UI ROUTES
    # ----------------------------------------------------
    @app.route("/")
    @login_required
    def index():
        return render_template("index.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")

        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("index"))

        return render_template("login.html", error="Invalid credentials")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    # ----------------------------------------------------
    # LIST RESTAURANTS
    # ----------------------------------------------------
    @app.route("/api/restaurants", methods=["GET"])
    @login_required
    def api_restaurants():
        qcountry = request.args.get("country")
        query = Restaurant.query

        # Restrict managers & members to their own country
        if current_user.role in ("manager", "member"):
            query = query.filter_by(country=current_user.country)
        elif qcountry:
            query = query.filter_by(country=qcountry)

        restaurants = query.all()

        return jsonify([
            {
                "id": r.id,
                "name": r.name,
                "country": r.country,
                "menu": [
                    {"id": m.id, "name": m.name, "price": m.price}
                    for m in r.menu_items
                ]
            }
            for r in restaurants
        ])

    # ----------------------------------------------------
    # ADD TO CART
    # ----------------------------------------------------
    @app.route("/api/cart/add", methods=["POST"])
    @login_required
    def api_cart_add():
        data = request.get_json(silent=True) or {}

        restaurant_id = data.get("restaurant_id")
        menu_item_id = data.get("menu_item_id")
        qty = int(data.get("qty", 1))

        if not restaurant_id or not menu_item_id:
            return jsonify({"error": "Missing fields"}), 400

        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return jsonify({"error": "Restaurant not found"}), 404

        # Restrict to country
        if current_user.role in ("manager", "member") and restaurant.country != current_user.country:
            return jsonify({"error": "Country restriction"}), 403

        # Existing cart?
        cart = Order.query.filter_by(
            user_id=current_user.id,
            restaurant_id=restaurant_id,
            status="cart"
        ).first()

        # Create cart if none exists
        if not cart:
            cart = Order(
                user_id=current_user.id,
                restaurant_id=restaurant_id,
                status="cart",
                country=restaurant.country,
                added_by=current_user.username
            )
            db.session.add(cart)
            db.session.commit()

        item = MenuItem.query.get(menu_item_id)
        if not item:
            return jsonify({"error": "Invalid item"}), 400

        order_item = OrderItem(order_id=cart.id, menu_item_id=item.id, qty=qty)
        db.session.add(order_item)

        # Update total
        db.session.flush()
        cart.total = sum(i.menu_item.price * i.qty for i in cart.items)
        db.session.commit()

        return jsonify({"message": "Added", "order_id": cart.id})

    # ----------------------------------------------------
    # CHECKOUT
    # ----------------------------------------------------
    @app.route("/api/checkout", methods=["POST"])
    @login_required
    def api_checkout():
        data = request.get_json(silent=True) or {}

        order_id = data.get("order_id")
        pm_id = data.get("payment_method_id")

        if not order_id or not pm_id:
            return jsonify({"error": "Missing fields"}), 400

        order = Order.query.get(order_id)

        if not order or order.user_id != current_user.id:
            return jsonify({"error": "Order not found"}), 404

        # Members cannot checkout
        if current_user.role == "member":
            return jsonify({"error": "Members cannot checkout"}), 403

        # Country lock
        if current_user.role == "manager" and order.country != current_user.country:
            return jsonify({"error": "Country restriction"}), 403

        # Recalculate total
        order.total = sum(i.menu_item.price * i.qty for i in order.items)

        # Validate payment method
        pm = PaymentMethod.query.get(pm_id)
        if not pm:
            return jsonify({"error": "Invalid payment method"}), 404

        if pm.user_id != current_user.id and current_user.role != "admin":
            return jsonify({"error": "Not allowed"}), 403

        # Place order
        order.status = "placed"
        db.session.commit()

        return jsonify({"message": "Order placed", "order_id": order.id})

    # ----------------------------------------------------
    # CANCEL ORDER
    # ----------------------------------------------------
    @app.route("/api/order/<int:oid>/cancel", methods=["POST"])
    @login_required
    def api_cancel(oid):
        order = Order.query.get(oid)
        if not order:
            return jsonify({"error": "Not found"}), 404

        if current_user.role == "member":
            return jsonify({"error": "Members cannot cancel"}), 403

        if current_user.role == "manager" and order.country != current_user.country:
            return jsonify({"error": "Country restricted"}), 403

        order.status = "cancelled"
        order.cancelled_by = current_user.username
        db.session.commit()

        return jsonify({"message": "Cancelled"})

    # ----------------------------------------------------
    # PAYMENT METHODS
    # FIXED GET HANDLER (no JSON parsing)
    # ----------------------------------------------------
    @app.route("/api/payment-methods", methods=["GET", "POST"])
    @login_required
    def api_payment_methods():

        # GET (list)
        if request.method == "GET":
            if current_user.role == "admin" and request.args.get("all") == "1":
                pms = PaymentMethod.query.all()
            else:
                pms = PaymentMethod.query.filter_by(user_id=current_user.id).all()

            return jsonify([
                {
                    "id": p.id,
                    "method_name": p.method_name,
                    "card_last4": p.card_last4
                }
                for p in pms
            ])

        # POST → Add new method
        data = request.get_json(silent=True) or {}

        method_name = data.get("method_name", "Card")
        card_last4 = data.get("card_last4", "0000")

        pm = PaymentMethod(
            user_id=current_user.id,
            method_name=method_name,
            card_last4=card_last4
        )

        db.session.add(pm)
        db.session.commit()

        return jsonify({"message": "Added", "id": pm.id})

    # ----------------------------------------------------
    # MY ORDERS
    # ----------------------------------------------------
    @app.route("/api/myorders", methods=["GET"])
    @login_required
    def api_myorders():

        # Admin view everything
        if current_user.role == "admin" and request.args.get("all") == "1":
            orders = Order.query.all()
        else:
            if current_user.role in ("manager", "member"):
                orders = Order.query.join(Restaurant).filter(
                    Restaurant.country == current_user.country
                ).all()
            else:
                orders = Order.query.filter_by(user_id=current_user.id).all()

        return jsonify([
            {
                "id": o.id,
                "restaurant": o.restaurant.name if o.restaurant else None,
                "restaurant_id": o.restaurant_id,
                "country": o.country,
                "status": o.status,
                "total": o.total,
                "items": [
                    {
                        "name": i.menu_item.name,
                        "qty": i.qty,
                        "price": i.menu_item.price
                    }
                    for i in o.items
                ],
                "added_by": o.added_by,
                "cancelled_by": o.cancelled_by,
                "created_at": o.created_at.isoformat()
            }
            for o in orders
        ])

    # END create_app
    return app


# ----------------------------------------------------
# LOCAL RUN
# ----------------------------------------------------
