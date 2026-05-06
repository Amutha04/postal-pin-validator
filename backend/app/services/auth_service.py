from functools import wraps
from flask import request, jsonify, g
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from config import Config
from app.models.user_model import get_user_by_id

TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
serializer = URLSafeTimedSerializer(Config.SECRET_KEY)


def create_token(user_id):
    return serializer.dumps({"user_id": str(user_id)}, salt="auth-token")


def verify_token(token):
    data = serializer.loads(
        token,
        salt="auth-token",
        max_age=TOKEN_MAX_AGE_SECONDS
    )
    return data.get("user_id")


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Authentication required"}), 401

        token = header.replace("Bearer ", "", 1).strip()
        try:
            user_id = verify_token(token)
        except SignatureExpired:
            return jsonify({"error": "Session expired"}), 401
        except BadSignature:
            return jsonify({"error": "Invalid session"}), 401

        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 401

        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper
