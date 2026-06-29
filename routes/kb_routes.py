"""KB article routes — mirrors /api/now/table/kb_knowledge in real ServiceNow."""

from flask import Blueprint, jsonify, request

from security.auth import auth_required
from services.kb_service import KBService


kb_blueprint = Blueprint("kb", __name__)


@kb_blueprint.get("/api/now/table/kb_knowledge")
@auth_required
def kb_list():
    return jsonify({"result": KBService.list_articles(request.args)}), 200


@kb_blueprint.post("/api/now/table/kb_knowledge")
@auth_required
def kb_create():
    data = request.get_json(silent=True) or {}
    return jsonify({"result": KBService.create_article(data)}), 201


@kb_blueprint.get("/api/now/table/kb_knowledge/<string:sys_id>")
@auth_required
def kb_get(sys_id):
    fields   = request.args.get("sysparm_fields")
    article  = KBService.get_article(sys_id, fields)
    if not article:
        return jsonify({"error": {"message": "KB article not found"}}), 404
    return jsonify({"result": article}), 200
