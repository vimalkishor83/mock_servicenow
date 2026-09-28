from flask import Blueprint, jsonify, request


OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Mock ServiceNow API Server",
        "version": "1.0.0",
        "description": "ServiceNow-compatible mock REST APIs for integration testing.",
    },
    "servers": [{"url": "http://localhost:8080"}],
    "components": {
        "securitySchemes": {
            "basicAuth": {"type": "http", "scheme": "basic"},
            "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
        }
    },
    "security": [{"basicAuth": []}, {"bearerAuth": []}],
    "paths": {
        "/api/auth/token": {
            "post": {
                "summary": "Issue JWT bearer token",
                "responses": {"200": {"description": "Token issued"}},
            }
        },
        "/api/now/table/incident": {
            "get": {
                "summary": "List incidents",
                "parameters": [
                    {"name": "sysparm_limit", "in": "query", "schema": {"type": "integer"}},
                    {"name": "sysparm_offset", "in": "query", "schema": {"type": "integer"}},
                    {"name": "sysparm_query", "in": "query", "schema": {"type": "string"}},
                    {"name": "sysparm_fields", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {"200": {"description": "Incident list"}},
            },
            "post": {
                "summary": "Create incident",
                "responses": {"201": {"description": "Incident created"}},
            },
        },
        "/api/now/table/incident/{sys_id}": {
            "get": {
                "summary": "Get incident by sys_id",
                "parameters": [{"name": "sys_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Incident"}},
            },
            "put": {
                "summary": "Update incident",
                "parameters": [{"name": "sys_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Incident updated"}},
            },
            "delete": {
                "summary": "Delete incident",
                "parameters": [{"name": "sys_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Incident deleted"}},
            },
        },
        "/api/now/table/sys_user": {
            "get": {"summary": "List users", "responses": {"200": {"description": "Users"}}},
            "post": {"summary": "Create user", "responses": {"201": {"description": "User created"}}},
        },
        "/api/now/table/sys_user_group": {
            "get": {"summary": "List assignment groups", "responses": {"200": {"description": "Groups"}}}
        },
    },
}


def register_swagger(app):
    @app.get("/swagger.json")
    def swagger_json():
        spec = dict(OPENAPI_SPEC)
        spec["servers"] = [{"url": request.script_root or "/"}]
        return jsonify(spec)

    try:
        from flask_swagger_ui import get_swaggerui_blueprint

        # flask_swagger_ui bakes base_url into its index page at *build* time
        # (when this function runs), so it has no way to see the per-request
        # reverse-proxy prefix -- everything it serves would 404 under one.
        # Registering this route BEFORE the library's blueprint below makes
        # Flask match it first for GET /swagger/, so it overrides just the
        # index page with our own, request-aware version; the blueprint
        # still serves its static JS/CSS/font assets correctly underneath.
        @app.get("/swagger/")
        def swagger_index():
            prefix = request.script_root or ""
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Mock ServiceNow API Server</title>
  <link rel="stylesheet" type="text/css" href="{prefix}/swagger/index.css">
  <link rel="stylesheet" type="text/css" href="{prefix}/swagger/swagger-ui.css">
  <link rel="icon" type="image/png" href="{prefix}/swagger/favicon-32x32.png" sizes="32x32" />
  <link rel="icon" type="image/png" href="{prefix}/swagger/favicon-16x16.png" sizes="16x16" />
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="{prefix}/swagger/swagger-ui-bundle.js"></script>
  <script src="{prefix}/swagger/swagger-ui-standalone-preset.js"></script>
  <script>
    var config = {{
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
      plugins: [SwaggerUIBundle.plugins.DownloadUrl],
      dom_id: "#swagger-ui",
      url: "{prefix}/swagger.json",
      layout: "StandaloneLayout",
      deepLinking: true
    }};
    window.onload = function () {{ window.ui = SwaggerUIBundle(config); }};
  </script>
</body>
</html>"""

        swagger_ui = get_swaggerui_blueprint(
            "/swagger",
            "swagger.json",
            config={"app_name": "Mock ServiceNow API Server"},
        )
        app.register_blueprint(swagger_ui, url_prefix="/swagger")

    except ImportError:
        fallback = Blueprint("swagger_fallback", __name__)

        @fallback.get("/swagger")
        def swagger_fallback():
            return (
                "<h1>Mock ServiceNow API Server</h1>"
                "<p>Install flask-swagger-ui to enable interactive Swagger UI.</p>"
                '<p><a href="../swagger.json">OpenAPI JSON</a></p>'
            )

        app.register_blueprint(fallback)
