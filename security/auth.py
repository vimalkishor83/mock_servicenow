from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, jsonify, request

from models.db_models import User


def generate_token(user):
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=current_app.config["JWT_EXPIRATION_MINUTES"]
    )
    payload = {
        "sub": user.sys_id,
        "username": user.user_name,
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )


def authenticate_basic(username, password):
    if not username or not password:
        return None
    user = User.query.filter_by(user_name=username, active=True).first()
    if user and user.verify_password(password):
        return user
    return None


def authenticate_request():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET_KEY"],
                algorithms=[current_app.config["JWT_ALGORITHM"]],
            )
        except jwt.PyJWTError:
            return None
        return User.query.filter_by(sys_id=payload.get("sub"), active=True).first()

    basic_auth = request.authorization
    if basic_auth:
        return authenticate_basic(basic_auth.username, basic_auth.password)
    return None


def auth_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_app.config.get("ENABLE_AUTH", True):
            request.current_user = None
            return func(*args, **kwargs)

        user = authenticate_request()
        if not user:
            response = jsonify(
                {
                    "error": {
                        "message": "Authentication required",
                        "detail": "Use HTTP Basic credentials or a Bearer token.",
                    }
                }
            )
            response.status_code = 401
            response.headers["WWW-Authenticate"] = 'Basic realm="Mock ServiceNow"'
            return response

        request.current_user = user
        return func(*args, **kwargs)

    return wrapper
