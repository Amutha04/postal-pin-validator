from flask import Blueprint, request, jsonify, g
from pymongo.errors import DuplicateKeyError
from app.models.user_model import (
    create_user,
    get_user_by_email,
    serialize_user,
    verify_user_password,
)
from app.services.auth_service import create_token, require_auth

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    try:
        user = create_user(name, email, password)
    except DuplicateKeyError:
        return jsonify({"error": "Email already registered"}), 409

    token = create_token(user["id"])
    return jsonify({"user": user, "token": token}), 201


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user_doc = get_user_by_email(email)
    if not user_doc or not verify_user_password(user_doc, password):
        return jsonify({"error": "Invalid email or password"}), 401

    user = serialize_user(user_doc)
    token = create_token(user["id"])
    return jsonify({"user": user, "token": token}), 200


@auth_bp.route("/auth/me", methods=["GET"])
@require_auth
def me():
    return jsonify({"user": serialize_user(g.current_user)}), 200
