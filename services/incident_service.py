import logging
import random
import re
from datetime import datetime, timedelta

from sqlalchemy import and_, func

from models.db_models import AssignmentGroup, Incident, User, db, utc_now

log = logging.getLogger(__name__)


INCIDENT_THEMES = [
    ("Database listener down", "Database failures", "database", "connectivity"),
    ("Disk space threshold exceeded", "Disk space issues", "inquiry", "storage"),
    ("External API returned 500 errors", "API failures", "software", "api"),
    ("Application memory leak detected", "Memory leaks", "software", "performance"),
    ("Repeated login failures", "Authentication failures", "security", "authentication"),
    ("Packet loss on core network", "Network failures", "network", "latency"),
    ("Nightly batch job failed", "Batch failures", "software", "batch"),
    ("Application process crashed", "Application crashes", "software", "runtime"),
]


OPERATORS = [">=", "<=", "!=", ">", "<", "="]


def parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


class IncidentService:
    @staticmethod
    def list_incidents(args):
        limit = min(int(args.get("sysparm_limit", 100)), 10000)
        offset = max(int(args.get("sysparm_offset", 0)), 0)
        fields = IncidentService._parse_fields(args.get("sysparm_fields"))

        query = Incident.query
        sysparm_query = args.get("sysparm_query")
        if sysparm_query:
            query = IncidentService._apply_sysparm_query(query, sysparm_query)

        incidents = (
            query.order_by(Incident.opened_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [incident.to_dict(fields) for incident in incidents]

    @staticmethod
    def get_incident(sys_id, fields=None):
        incident = Incident.query.filter_by(sys_id=sys_id).first()
        if not incident:
            return None
        return incident.to_dict(IncidentService._parse_fields(fields))

    @staticmethod
    def create_incident(data):
        incident = Incident(
            number=IncidentService.next_incident_number(),
            short_description=data.get("short_description") or "No short description",
            description=data.get("description"),
            category=data.get("category"),
            subcategory=data.get("subcategory"),
            priority=str(data.get("priority", "3")),
            urgency=str(data.get("urgency", "3")),
            impact=str(data.get("impact", "3")),
            assignment_group=data.get("assignment_group"),
            assigned_to=data.get("assigned_to"),
            state=data.get("state", "New"),
            opened_at=parse_datetime(data.get("opened_at", "")) or utc_now(),
            opened_by=data.get("opened_by"),
            resolved_at=parse_datetime(data.get("resolved_at", "")),
            resolved_by=data.get("resolved_by"),
            close_notes=data.get("close_notes"),
            work_notes=data.get("work_notes"),
            comments=data.get("comments"),
            caller_id=data.get("caller_id"),
        )
        if incident.state not in Incident.VALID_STATES:
            incident.state = "New"
        db.session.add(incident)
        db.session.commit()
        log.info('Incident created: number=%s state=%s priority=%s', incident.number, incident.state, incident.priority)
        return incident.to_dict()

    @staticmethod
    def update_incident(sys_id, data):
        incident = Incident.query.filter_by(sys_id=sys_id).first()
        if not incident:
            return None

        writable_fields = set(Incident.SERVICENOW_FIELDS) - {"sys_id", "number"}
        for field in writable_fields:
            if field not in data:
                continue
            value = data[field]
            if field in {"opened_at", "resolved_at"}:
                value = parse_datetime(value) if value else None
            elif field in {"priority", "urgency", "impact"}:
                value = str(value)
            setattr(incident, field, value)

        if incident.state == "Resolved" and not incident.resolved_at:
            incident.resolved_at = utc_now()
        db.session.commit()
        log.info('Incident updated: number=%s state=%s', incident.number, incident.state)
        return incident.to_dict()

    @staticmethod
    def delete_incident(sys_id):
        incident = Incident.query.filter_by(sys_id=sys_id).first()
        if not incident:
            return False
        db.session.delete(incident)
        db.session.commit()
        log.info('Incident deleted: sys_id=%s', sys_id)
        return True

    @staticmethod
    def next_incident_number():
        max_number = db.session.query(func.max(Incident.number)).scalar()
        if not max_number:
            return "INC0001001"
        match = re.search(r"(\d+)$", max_number)
        next_value = int(match.group(1)) + 1 if match else 1001
        return f"INC{next_value:07d}"

    @staticmethod
    def create_random_incident():
        groups = AssignmentGroup.query.all()
        users = User.query.filter_by(active=True).all()
        title, description, category, subcategory = random.choice(INCIDENT_THEMES)
        state = random.choices(
            ["New", "In Progress", "On Hold", "Resolved", "Closed", "Cancelled"],
            weights=[25, 35, 10, 20, 8, 2],
        )[0]
        priority = random.choices(["1", "2", "3", "4", "5"], weights=[8, 18, 42, 24, 8])[0]
        group = random.choice(groups).name if groups else None
        caller = random.choice(users).name if users else "System"
        assigned_to = random.choice(users).name if users and state != "New" else None
        opened_at = utc_now() - timedelta(minutes=random.randint(0, 60 * 24 * 45))
        resolved_at = utc_now() if state in {"Resolved", "Closed"} else None

        return IncidentService.create_incident(
            {
                "short_description": title,
                "description": description,
                "category": category,
                "subcategory": subcategory,
                "priority": priority,
                "urgency": priority if priority in {"1", "2"} else str(random.randint(2, 4)),
                "impact": priority if priority in {"1", "2"} else str(random.randint(2, 4)),
                "assignment_group": group,
                "assigned_to": assigned_to,
                "state": state,
                "opened_at": opened_at.strftime("%Y-%m-%d %H:%M:%S"),
                "opened_by": caller,
                "resolved_at": resolved_at.strftime("%Y-%m-%d %H:%M:%S") if resolved_at else None,
                "resolved_by": assigned_to if resolved_at else None,
                "close_notes": "Issue remediated and validated." if resolved_at else None,
                "work_notes": "Automated enterprise activity simulation.",
                "comments": "Generated by mock ServiceNow scheduler.",
                "caller_id": caller,
            }
        )

    @staticmethod
    def dashboard_summary():
        total = Incident.query.count()
        open_count = Incident.query.filter(Incident.state.in_(["New", "In Progress", "On Hold"])).count()
        resolved = Incident.query.filter_by(state="Resolved").count()
        critical = Incident.query.filter_by(priority="1").count()
        latest = Incident.query.order_by(Incident.opened_at.desc()).limit(10).all()

        trend = []
        today = utc_now().date()
        for days_back in range(6, -1, -1):
            day = today - timedelta(days=days_back)
            next_day = day + timedelta(days=1)
            count = Incident.query.filter(
                and_(Incident.opened_at >= day, Incident.opened_at < next_day)
            ).count()
            trend.append({"date": day.isoformat(), "count": count})

        by_state = {}
        for state in ["New", "In Progress", "On Hold", "Resolved", "Closed", "Cancelled"]:
            by_state[state] = Incident.query.filter_by(state=state).count()

        by_priority = {}
        for p in [1, 2, 3, 4, 5]:
            by_priority[p] = Incident.query.filter_by(priority=str(p)).count()

        return {
            "total": total,
            "open": open_count,
            "resolved": resolved,
            "critical": critical,
            "trend": trend,
            "by_state": by_state,
            "by_priority": by_priority,
            "latest": [item.to_dict() for item in latest],
        }

    @staticmethod
    def _parse_fields(raw_fields):
        if not raw_fields:
            return None
        return [field.strip() for field in raw_fields.split(",") if field.strip()]

    @staticmethod
    def _apply_sysparm_query(query, raw_query):
        clauses = [clause.strip() for clause in raw_query.split("^") if clause.strip()]
        for clause in clauses:
            parsed = IncidentService._parse_clause(clause)
            if not parsed:
                continue
            field, operator, raw_value = parsed
            column = getattr(Incident, field, None)
            if column is None:
                continue
            value = raw_value.strip()
            if field in {"opened_at", "resolved_at"}:
                value = parse_datetime(value) or value
            query = query.filter(IncidentService._build_filter(column, operator, value))
        return query

    @staticmethod
    def _parse_clause(clause):
        for operator in OPERATORS:
            if operator in clause:
                field, value = clause.split(operator, 1)
                return field.strip(), operator, value.strip()
        return None

    @staticmethod
    def _build_filter(column, operator, value):
        if operator == "=":
            return column == value
        if operator == "!=":
            return column != value
        if operator == ">=":
            return column >= value
        if operator == "<=":
            return column <= value
        if operator == ">":
            return column > value
        if operator == "<":
            return column < value
        return column == value
