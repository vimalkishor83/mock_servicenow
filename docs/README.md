# Mock ServiceNow API Server

`mock_servicenow` is a Python Flask server that simulates ServiceNow table APIs for local integration testing. Applications can integrate with this mock using the same base URL, username, and password pattern they would use for a real ServiceNow instance.

## Features

- ServiceNow-like REST URLs under `/api/now/table`
- Basic Authentication with database-backed credentials
- JWT Bearer token authentication
- SQLite database by default through SQLAlchemy ORM
- Configurable database connection string for later SQL Server or Oracle migration
- ServiceNow-style response envelope: `{"result": ...}`
- ServiceNow-style query filtering with `^` AND expressions
- Swagger UI at `/swagger`
- Web dashboard at `/dashboard`
- Request logging to `logs/application.log`
- Automatic dummy data generation:
  - 100 users
  - 10 assignment groups
  - 5000 incidents
- Background scheduler that creates random incidents every 5 minutes

## Setup

```powershell
cd mock_servicenow
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

The server runs on:

```text
http://localhost:8080
```

Default credentials:

```text
Username: admin
Password: admin123
```

## Configuration

Edit `config.py` or set environment variables:

```text
HOST=0.0.0.0
PORT=8080
DB_CONNECTION_STRING=sqlite:///database/mock_snow.db
ENABLE_AUTH=True
JWT_SECRET_KEY=change-this-secret-for-non-local-use
AUTO_SEED_DUMMY_DATA=True
ENABLE_SCHEDULER=True
SCHEDULER_INTERVAL_SECONDS=300
```

For SQL Server or Oracle later, replace `DB_CONNECTION_STRING` with the proper SQLAlchemy URL and install the corresponding database driver.

## Authentication

All table APIs support HTTP Basic Auth:

```powershell
curl.exe -u admin:admin123 "http://localhost:8080/api/now/table/incident?sysparm_limit=10"
```

To issue a JWT:

```powershell
curl.exe -u admin:admin123 -X POST "http://localhost:8080/api/auth/token"
```

Then call APIs with:

```powershell
curl.exe -H "Authorization: Bearer <token>" "http://localhost:8080/api/now/table/incident?sysparm_limit=10"
```

## Incident APIs

```text
GET    /api/now/table/incident
GET    /api/now/table/incident/{sys_id}
POST   /api/now/table/incident
PUT    /api/now/table/incident/{sys_id}
DELETE /api/now/table/incident/{sys_id}
```

Supported query parameters:

```text
sysparm_limit
sysparm_offset
sysparm_query
sysparm_fields
```

Examples:

```text
/api/now/table/incident?sysparm_limit=10
/api/now/table/incident?sysparm_query=state=Resolved
/api/now/table/incident?sysparm_query=priority=1
/api/now/table/incident?sysparm_query=assignment_group=Database Team
/api/now/table/incident?sysparm_query=opened_at>=2026-01-01
/api/now/table/incident?sysparm_query=state=Resolved^priority=1
/api/now/table/incident?sysparm_fields=sys_id,number,state,priority
```

Create incident:

```powershell
curl.exe -u admin:admin123 `
  -H "Content-Type: application/json" `
  -X POST "http://localhost:8080/api/now/table/incident" `
  -d "{\"short_description\":\"Database listener down\",\"priority\":\"1\",\"state\":\"New\",\"assignment_group\":\"Database Team\"}"
```

## User and Group APIs

```text
GET  /api/now/table/sys_user
POST /api/now/table/sys_user
GET  /api/now/table/sys_user_group
```

## Client Compatibility Example

Applications should depend only on URL and credentials:

```python
import requests


class ServiceNowClient:
    def __init__(self, url, username, password):
        self.url = url.rstrip("/")
        self.username = username
        self.password = password

    def list_incidents(self, query=None, limit=10):
        params = {"sysparm_limit": limit}
        if query:
            params["sysparm_query"] = query
        response = requests.get(
            f"{self.url}/api/now/table/incident",
            params=params,
            auth=(self.username, self.password),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["result"]


client = ServiceNowClient(
    url="http://localhost:8080",
    username="admin",
    password="admin123",
)

incidents = client.list_incidents("state=Resolved^priority=1", limit=10)
```

To move from the mock server to real ServiceNow, change only:

```text
SNOW_URL
SNOW_USERNAME
SNOW_PASSWORD
```

## Swagger and Dashboard

```text
Swagger UI: http://localhost:8080/swagger
Dashboard:  http://localhost:8080/dashboard
```

## Regenerate Dummy Data

```powershell
cd mock_servicenow
python scripts/generate_dummy_data.py
```
