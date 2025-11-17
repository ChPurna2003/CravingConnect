# backend/auth.py
from functools import wraps
from flask_login import current_user
from flask import jsonify

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Authentication required"}), 401
            if current_user.role not in allowed_roles:
                return jsonify({"error": "You do not have permission"}), 403
            return f(*args, **kwargs)
        return wrapped
    return decorator

def role_or_admin(allowed_roles):
    # allow admin always, otherwise allowed_roles
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Authentication required"}), 401
            if current_user.role == "admin" or current_user.role in allowed_roles:
                return f(*args, **kwargs)
            return jsonify({"error": "You do not have permission"}), 403
        return wrapped
    return decorator

def enforce_country_scope(get_user_country_fn):
    """
    Wrapper to be used inside endpoints: verify that manager/member act only within their country.
    get_user_country_fn: function that returns country involved in request (restaurant country, or order restaurant country).
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Authentication required"}), 401
            # admin bypass
            if current_user.role == "admin":
                return f(*args, **kwargs)
            # for manager/member, ensure country matches
            target_country = get_user_country_fn(*args, **kwargs)
            if target_country and current_user.country != target_country:
                return jsonify({"error": "Access limited to your country"}), 403
            return f(*args, **kwargs)
        return wrapped
    return decorator
