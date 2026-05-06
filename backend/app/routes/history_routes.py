from flask import Blueprint, request, jsonify, g
from app.models.history_model import add_history, clear_history, list_history
from app.services.auth_service import require_auth

history_bp = Blueprint("history", __name__)


@history_bp.route("/history", methods=["GET"])
@require_auth
def get_history():
    return jsonify({"history": list_history(g.current_user["_id"])}), 200


@history_bp.route("/history", methods=["POST"])
@require_auth
def create_history():
    data = request.get_json() or {}
    rows = data.get("rows")
    if rows is None:
        rows = [data]
    if not isinstance(rows, list):
        return jsonify({"error": "History rows must be a list"}), 400

    saved = [add_history(g.current_user["_id"], row) for row in rows]
    return jsonify({"history": saved}), 201


@history_bp.route("/history", methods=["DELETE"])
@require_auth
def delete_history():
    clear_history(g.current_user["_id"])
    return jsonify({"ok": True}), 200
