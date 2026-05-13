from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt
)
from .extensions import db, bcrypt
from .models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# ── Blocklist for logged-out tokens (in-memory; use Redis in prod) ────────────
_token_blocklist = set()


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    POST /api/auth/register
    Body: { "username": "...", "email": "...", "password": "..." }
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    email    = data.get("email",    "").strip().lower()
    password = data.get("password", "")

    # ── Validation ────────────────────────────
    errors = {}
    if not username or len(username) < 3:
        errors["username"] = "At least 3 characters required."
    if "@" not in email:
        errors["email"] = "Valid email required."
    if len(password) < 6:
        errors["password"] = "At least 6 characters required."
    if errors:
        return jsonify({"error": "Validation failed", "fields": errors}), 422

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken."}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered."}), 409

    hashed = bcrypt.generate_password_hash(password).decode("utf-8")
    user   = User(username=username, email=email, password=hashed)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=user.id)
    return jsonify({
        "message": "Registered successfully.",
        "user":    user.to_dict(),
        "token":   token,
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/auth/login
    Body: { "username": "...", "password": "..." }
    """
    data     = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials."}), 401

    token = create_access_token(identity=user.id)
    return jsonify({
        "message": "Login successful.",
        "user":    user.to_dict(),
        "token":   token,
    }), 200


@auth_bp.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    """
    DELETE /api/auth/logout
    Header: Authorization: Bearer <token>
    Adds token to blocklist.
    """
    jti = get_jwt()["jti"]
    _token_blocklist.add(jti)
    return jsonify({"message": "Logged out successfully."}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """GET /api/auth/me — Returns current user's profile."""
    user_id = get_jwt_identity()
    user    = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200


def is_token_revoked(jwt_header, jwt_payload):
    """Called by JWTManager to check blocklist."""
    return jwt_payload.get("jti") in _token_blocklist
