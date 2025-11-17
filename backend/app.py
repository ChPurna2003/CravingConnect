# backend/app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import db, User, Restaurant, MenuItem, PaymentMethod, Order, OrderItem
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from auth import role_required, role_or_admin, enforce_country_scope
import os

def create_app():
    app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foodapp.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-secret")

    db.init_app(app)

    # Login manager
    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ------------------------------
    # ROUTES - UI
    # ------------------------------
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

    # ------------------------------------------
    # API: List restaurants + menus
    # ------------------------------------------
    @app.route("/api/restaurants", methods=["GET"])
    @login_required
    def api_restaurants():
        qcountry = request.args.get("country")
        query = Restaurant.query

        # Country restrictions for manager + member
        if current_user.role in ("manager", "member"):
            query = query.filter_by(country=current_user.country)
        elif qcountry:
            query = query.filter_by(country=qcountry)

        restaurants = query.all()
        out = []
        for r in restaurants:
            out.append({
                "id": r.id,
                "name": r.name,
                "country": r.country,
                "menu": [
                    {"id": m.id, "name": m.name, "price": m.price}
                    for m in r.menu_items
                ]
            })
        return jsonify(out)

    # ------------------------------------------
    # ADD TO CART
    # ------------------------------------------
    @app.route("/api/cart/add", methods=["POST"])
    @login_required
    def api_add_to_cart():
        data = request.get_json(silent=True) or {}
        restaurant_id = data.get("restaurant_id")
        menu_item_id = data.get("menu_item_id")
        try:
            qty = int(data.get("qty", 1))
        except (TypeError, ValueError):
            qty = 1

        if not restaurant_id or not menu_item_id:
            return jsonify({"error": "Missing restaurant_id or menu_item_id"}), 400

        rest = Restaurant.query.get(restaurant_id)
        if not rest:
            return jsonify({"error": "Restaurant not found"}), 404

        # Country restriction for manager + member
        if current_user.role in ("manager", "member") and rest.country != current_user.country:
            return jsonify({"error": "You cannot order outside your assigned country"}), 403

        # Find existing cart order for this user + restaurant
        cart = Order.query.filter_by(
            user_id=current_user.id,
            status="cart",
            restaurant_id=restaurant_id
        ).first()

        if not cart:
            cart = Order(
                user_id=current_user.id,
                restaurant_id=restaurant_id,
                country=rest.country,
                status="cart",
                added_by=current_user.username
            )
            db.session.add(cart)
            db.session.commit()  # commit so cart.id exists

        menu_item = MenuItem.query.get(menu_item_id)
        if not menu_item or menu_item.restaurant_id != restaurant_id:
            return jsonify({"error": "Invalid menu item"}), 400

        # Create order item
        oi = OrderItem(order_id=cart.id, menu_item_id=menu_item.id, qty=qty)
        db.session.add(oi)
        db.session.flush()  # ensure oi is associated so relationship contains it

        # Update total from relationship (includes flushed oi)
        cart.total = sum(i.menu_item.price * i.qty for i in cart.items)
        db.session.commit()

        return jsonify({"message": "Added", "order_id": cart.id})

    # ------------------------------------------
    # CHECKOUT
    # ------------------------------------------
    @app.route("/api/checkout", methods=["POST"])
    @login_required
    def api_checkout():
        data = request.get_json(silent=True) or {}
        order_id = data.get("order_id")
        pm_id = data.get("payment_method_id")

        if not order_id or not pm_id:
            return jsonify({"error": "Missing order_id or payment_method_id"}), 400

        order = Order.query.get(order_id)
        if not order or order.user_id != current_user.id:
            return jsonify({"error": "Order not found"}), 404

        # Member cannot checkout
        if current_user.role == "member":
            return jsonify({"error": "Members cannot checkout"}), 403

        # Manager country restriction
        if current_user.role == "manager" and order.country != current_user.country:
            return jsonify({"error": "You cannot checkout orders outside your country"}), 403

        if order.status != "cart":
            return jsonify({"error": "Order is not in cart"}), 400

        # Recalculate total (fresh)
        order.total = sum(item.menu_item.price * item.qty for item in order.items)

        # Validate payment method
        pm = PaymentMethod.query.get(pm_id)
        if not pm or (pm.user_id != current_user.id and current_user.role != "admin"):
            return jsonify({"error": "Invalid payment method"}), 403

        # Simulate payment success (you can integrate real gateway here)
        order.status = "placed"
        db.session.commit()

        return jsonify({"message": "Order placed", "order_id": order.id})

    # ------------------------------------------
    # CANCEL ORDER
    # ------------------------------------------
    @app.route("/api/order/<int:order_id>/cancel", methods=["POST"])
    @login_required
    def api_cancel_order(order_id):
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404

        # Member cannot cancel
        if current_user.role == "member":
            return jsonify({"error": "Members cannot cancel orders"}), 403

        # Manager restricted by country
        if current_user.role == "manager" and order.country != current_user.country:
            return jsonify({"error": "You cannot cancel orders outside your country"}), 403

        if order.status == "cancelled":
            return jsonify({"message": "Already cancelled"})

        # Set cancelled by user
        order.status = "cancelled"
        order.cancelled_by = current_user.username
        db.session.commit()

        return jsonify({"message": "Order cancelled"})

    # ------------------------------------------
    # PAYMENT METHODS
    # ------------------------------------------
    @app.route("/api/payment-methods", methods=["GET", "POST", "PUT"])
    @login_required
    def api_payment_methods():
        data = request.get_json(silent=True) or {}

        # GET LIST
        if request.method == "GET":
            if current_user.role == "admin" and request.args.get("all") == "1":
                pms = PaymentMethod.query.all()
            else:
                pms = PaymentMethod.query.filter_by(user_id=current_user.id).all()
            return jsonify([
                {
                    "id": p.id,
                    "user_id": p.user_id,
                    "method_name": p.method_name,
                    "card_last4": p.card_last4
                } for p in pms
            ])

        # ADD PAYMENT METHOD (POST)
        if request.method == "POST":
            target_uid = data.get("user_id") or current_user.id

            if current_user.role != "admin" and int(target_uid) != int(current_user.id):
                return jsonify({"error": "You cannot add methods for others"}), 403

            method_name = data.get("method_name", "Card")
            card_last4 = data.get("card_last4", "0000")

            pm = PaymentMethod(
                user_id=target_uid,
                method_name=method_name,
                card_last4=card_last4
            )
            db.session.add(pm)
            db.session.commit()
            return jsonify({"message": "Added", "id": pm.id})

        # UPDATE PAYMENT METHOD (PUT)
        if request.method == "PUT":
            pm_id = data.get("id")
            if not pm_id:
                return jsonify({"error": "Missing id for update"}), 400

            pm = PaymentMethod.query.get(pm_id)
            if not pm:
                return jsonify({"error": "Not found"}), 404

            if current_user.role != "admin" and pm.user_id != current_user.id:
                return jsonify({"error": "Not allowed"}), 403

            pm.method_name = data.get("method_name", pm.method_name)
            pm.card_last4 = data.get("card_last4", pm.card_last4)
            db.session.commit()

            return jsonify({"message": "Updated"})

    # ------------------------------------------
    # USER ORDERS
    # ------------------------------------------
    @app.route("/api/myorders", methods=["GET"])
    @login_required
    def api_myorders():

        # Admin can view all
        if current_user.role == "admin" and request.args.get("all") == "1":
            orders = Order.query.all()

        else:
            # managers and members see orders in their country (this shows all orders for that country)
            if current_user.role in ("manager", "member"):
                orders = Order.query.join(Restaurant).filter(
                    Restaurant.country == current_user.country
                ).all()
            else:
                # normal users see their own orders
                orders = Order.query.filter_by(user_id=current_user.id).all()

        out = []
        for o in orders:
            out.append({
                "id": o.id,
                "user_id": o.user_id,
                "restaurant": o.restaurant.name if o.restaurant else None,
                "restaurant_id": o.restaurant_id,
                "country": o.country,
                "status": o.status,
                "total": o.total,
                "added_by": o.added_by,
                "cancelled_by": o.cancelled_by,
                "items": [
                    {"name": it.menu_item.name, "qty": it.qty, "price": it.menu_item.price}
                    for it in o.items
                ],
                "created_at": o.created_at.isoformat() if o.created_at else None
            })
        return jsonify(out)

    return app


# --------------------------------------------------------
# RUN APP
# --------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
