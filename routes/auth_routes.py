from flask import Blueprint, current_app, jsonify, request

from security.auth import authenticate_basic, generate_token


auth_blueprint = Blueprint("auth", __name__)


@auth_blueprint.post("/api/auth/token")
def token():
    basic_auth = request.authorization
    data       = request.get_json(silent=True) or {}
    username   = basic_auth.username if basic_auth else data.get("username")
    password   = basic_auth.password if basic_auth else data.get("password")

    user = authenticate_basic(username, password)
    if not user:
        return jsonify({
            "error": {
                "message": "Invalid credentials",
                "detail": "Could not issue token for supplied credentials.",
            }
        }), 401

    return jsonify({
        "result": {
            "token_type":        "Bearer",
            "access_token":      generate_token(user),
            "expires_in_minutes": current_app.config["JWT_EXPIRATION_MINUTES"],
            "user":              user.to_dict(),
        }
    })
