from flask import Blueprint, jsonify, request

from security.auth import auth_required
from services.incident_service import IncidentService


incident_blueprint = Blueprint("incident", __name__)


@incident_blueprint.get("/api/now/table/incident")
@auth_required
def incident_list():
    return jsonify({"result": IncidentService.list_incidents(request.args)}), 200


@incident_blueprint.post("/api/now/table/incident")
@auth_required
def incident_create():
    data = request.get_json(silent=True) or {}
    return jsonify({"result": IncidentService.create_incident(data)}), 201


@incident_blueprint.get("/api/now/table/incident/<string:sys_id>")
@auth_required
def incident_get(sys_id):
    incident = IncidentService.get_incident(sys_id, request.args.get("sysparm_fields"))
    if not incident:
        return jsonify({"error": {"message": "Incident not found"}}), 404
    return jsonify({"result": incident}), 200


@incident_blueprint.put("/api/now/table/incident/<string:sys_id>")
@auth_required
def incident_update(sys_id):
    data = request.get_json(silent=True) or {}
    incident = IncidentService.update_incident(sys_id, data)
    if not incident:
        return jsonify({"error": {"message": "Incident not found"}}), 404
    return jsonify({"result": incident}), 200


@incident_blueprint.delete("/api/now/table/incident/<string:sys_id>")
@auth_required
def incident_delete(sys_id):
    deleted = IncidentService.delete_incident(sys_id)
    if not deleted:
        return jsonify({"error": {"message": "Incident not found"}}), 404
    return jsonify({"result": {"sys_id": sys_id, "deleted": True}}), 200
