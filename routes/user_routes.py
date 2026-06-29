from flask import Blueprint, jsonify, request

from security.auth import auth_required
from services.user_service import UserService


user_blueprint = Blueprint("user", __name__)


@user_blueprint.get("/api/now/table/sys_user")
@auth_required
def user_list():
    limit  = min(int(request.args.get("sysparm_limit", 100)), 10000)
    offset = max(int(request.args.get("sysparm_offset", 0)), 0)
    return jsonify({"result": UserService.list_users(limit, offset)}), 200


@user_blueprint.post("/api/now/table/sys_user")
@auth_required
def user_create():
    data = request.get_json(silent=True) or {}
    if not data.get("user_name"):
        return jsonify({"error": {"message": "user_name is required"}}), 400
    return jsonify({"result": UserService.create_user(data)}), 201


@user_blueprint.get("/api/now/table/sys_user_group")
@auth_required
def group_list():
    limit  = min(int(request.args.get("sysparm_limit", 100)), 10000)
    offset = max(int(request.args.get("sysparm_offset", 0)), 0)
    return jsonify({"result": UserService.list_groups(limit, offset)}), 200
