import uuid
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def new_sys_id():
    return uuid.uuid4().hex


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)


class User(db.Model, TimestampMixin):
    __tablename__ = "sys_user"

    sys_id = db.Column(db.String(32), primary_key=True, default=new_sys_id)
    user_name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    name = db.Column(db.String(180), nullable=False)
    email = db.Column(db.String(180), nullable=True, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    department = db.Column(db.String(120), nullable=True)
    title = db.Column(db.String(120), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "sys_id": self.sys_id,
            "user_name": self.user_name,
            "name": self.name,
            "email": self.email,
            "active": str(self.active).lower(),
            "department": self.department,
            "title": self.title,
        }


class AssignmentGroup(db.Model, TimestampMixin):
    __tablename__ = "sys_user_group"

    sys_id = db.Column(db.String(32), primary_key=True, default=new_sys_id)
    name = db.Column(db.String(180), nullable=False, unique=True, index=True)
    description = db.Column(db.String(500), nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {
            "sys_id": self.sys_id,
            "name": self.name,
            "description": self.description,
            "active": str(self.active).lower(),
        }


class Incident(db.Model, TimestampMixin):
    __tablename__ = "incident"

    sys_id = db.Column(db.String(32), primary_key=True, default=new_sys_id)
    number = db.Column(db.String(20), nullable=False, unique=True, index=True)
    short_description = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    subcategory = db.Column(db.String(100), nullable=True)
    priority = db.Column(db.String(10), nullable=False, default="3", index=True)
    urgency = db.Column(db.String(10), nullable=False, default="3")
    impact = db.Column(db.String(10), nullable=False, default="3")
    assignment_group = db.Column(db.String(180), nullable=True, index=True)
    assigned_to = db.Column(db.String(180), nullable=True)
    state = db.Column(db.String(40), nullable=False, default="New", index=True)
    opened_at = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)
    opened_by = db.Column(db.String(180), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.String(180), nullable=True)
    close_notes = db.Column(db.Text, nullable=True)
    work_notes = db.Column(db.Text, nullable=True)
    comments = db.Column(db.Text, nullable=True)
    caller_id = db.Column(db.String(180), nullable=True)

    SERVICENOW_FIELDS = [
        "sys_id",
        "number",
        "short_description",
        "description",
        "category",
        "subcategory",
        "priority",
        "urgency",
        "impact",
        "assignment_group",
        "assigned_to",
        "state",
        "opened_at",
        "opened_by",
        "resolved_at",
        "resolved_by",
        "close_notes",
        "work_notes",
        "comments",
        "caller_id",
    ]

    VALID_STATES = {"New", "In Progress", "On Hold", "Resolved", "Closed", "Cancelled"}

    def to_dict(self, fields=None):
        data = {
            "sys_id": self.sys_id,
            "number": self.number,
            "short_description": self.short_description,
            "description": self.description,
            "category": self.category,
            "subcategory": self.subcategory,
            "priority": self.priority,
            "urgency": self.urgency,
            "impact": self.impact,
            "assignment_group": self.assignment_group,
            "assigned_to": self.assigned_to,
            "state": self.state,
            "opened_at": self._format_dt(self.opened_at),
            "opened_by": self.opened_by,
            "resolved_at": self._format_dt(self.resolved_at),
            "resolved_by": self.resolved_by,
            "close_notes": self.close_notes,
            "work_notes": self.work_notes,
            "comments": self.comments,
            "caller_id": self.caller_id,
        }
        if fields:
            allowed = {field.strip() for field in fields if field.strip()}
            return {key: value for key, value in data.items() if key in allowed}
        return data

    @staticmethod
    def _format_dt(value):
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


class KBArticle(db.Model, TimestampMixin):
    """Knowledge Base article — mirrors ServiceNow kb_knowledge table."""

    __tablename__ = "kb_knowledge"

    sys_id           = db.Column(db.String(32),  primary_key=True, default=new_sys_id)
    number           = db.Column(db.String(20),  nullable=False, unique=True, index=True)
    short_description = db.Column(db.String(255), nullable=False)
    text             = db.Column(db.Text,         nullable=True)   # Article body / resolution steps
    category         = db.Column(db.String(100),  nullable=True)
    keywords         = db.Column(db.String(300),  nullable=True)
    assignment_group = db.Column(db.String(180),  nullable=True, index=True)
    author           = db.Column(db.String(180),  nullable=True)
    active           = db.Column(db.Boolean,      nullable=False, default=True)
    view_count       = db.Column(db.Integer,      nullable=False, default=0)

    VALID_FIELDS = [
        "sys_id", "number", "short_description", "text", "category",
        "keywords", "assignment_group", "author", "active", "view_count",
    ]

    def to_dict(self, fields=None):
        data = {
            "sys_id":            self.sys_id,
            "number":            self.number,
            "short_description": self.short_description,
            "text":              self.text,
            "category":          self.category,
            "keywords":          self.keywords,
            "assignment_group":  self.assignment_group,
            "author":            self.author,
            "active":            str(self.active).lower(),
            "view_count":        self.view_count,
        }
        if fields:
            allowed = {f.strip() for f in fields if f.strip()}
            return {k: v for k, v in data.items() if k in allowed}
        return data
