"""
Browser-facing UI routes for the mock ServiceNow server.
Provides searchable list + detail pages for Incidents and KB Articles.
"""

from flask import Blueprint, render_template, request, abort
from sqlalchemy import or_

from models.db_models import AssignmentGroup, Incident, KBArticle, db

ui_blueprint = Blueprint("ui", __name__)

PAGE_SIZE = 25


# ── Dashboard ─────────────────────────────────────────────────────────────────

@ui_blueprint.get("/")
@ui_blueprint.get("/dashboard")
def dashboard():
    from services.incident_service import IncidentService
    summary     = IncidentService.dashboard_summary()
    kb_articles = (
        KBArticle.query
        .filter_by(active=True)
        .order_by(KBArticle.view_count.desc())
        .limit(6)
        .all()
    )
    return render_template(
        "dashboard.html",
        summary     = summary,
        kb_count    = KBArticle.query.count(),
        kb_articles = [a.to_dict() for a in kb_articles],
    )


# ── Incidents ─────────────────────────────────────────────────────────────────

@ui_blueprint.get("/ui/incidents")
def incidents():
    q        = request.args.get("q", "").strip()
    state    = request.args.get("state", "").strip()
    priority = request.args.get("priority", "").strip()
    group    = request.args.get("group", "").strip()
    page     = max(int(request.args.get("page", 1)), 1)

    query = Incident.query

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Incident.number.ilike(like),
                Incident.short_description.ilike(like),
                Incident.description.ilike(like),
            )
        )
    if state:
        query = query.filter(Incident.state == state)
    if priority:
        query = query.filter(Incident.priority == int(priority))
    if group:
        query = query.filter(Incident.assignment_group == group)

    total     = query.count()
    pages     = max((total + PAGE_SIZE - 1) // PAGE_SIZE, 1)
    page      = min(page, pages)
    incidents = (
        query.order_by(Incident.created_at.desc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
        .all()
    )

    # Build the query string without 'page' for pagination links
    qs_parts = []
    for k in ("q", "state", "priority", "group"):
        v = request.args.get(k, "")
        if v:
            qs_parts.append(f"{k}={v}")
    query_string = "&".join(qs_parts)

    return render_template(
        "incidents.html",
        incidents    = [i.to_dict() for i in incidents],
        total        = total,
        page         = page,
        pages        = pages,
        query_string = query_string,
        q=q, state=state, priority=priority, group=group,
        states    = _incident_states(),
        priorities= [1, 2, 3, 4, 5],
        groups    = _group_names(),
    )


@ui_blueprint.get("/ui/incidents/<string:number>")
def incident_detail(number):
    inc = Incident.query.filter_by(number=number).first()
    if not inc:
        abort(404)
    return render_template("incident_detail.html", incident=inc.to_dict())


# ── Knowledge Base ────────────────────────────────────────────────────────────

@ui_blueprint.get("/ui/kb")
def kb_list():
    q        = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    group    = request.args.get("group", "").strip()
    page     = max(int(request.args.get("page", 1)), 1)

    query = KBArticle.query.filter_by(active=True)

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                KBArticle.short_description.ilike(like),
                KBArticle.keywords.ilike(like),
                KBArticle.text.ilike(like),
                KBArticle.category.ilike(like),
            )
        )
    if category:
        query = query.filter(KBArticle.category == category)
    if group:
        query = query.filter(KBArticle.assignment_group == group)

    total    = query.count()
    pages    = max((total + PAGE_SIZE - 1) // PAGE_SIZE, 1)
    page     = min(page, pages)
    articles = (
        query.order_by(KBArticle.view_count.desc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
        .all()
    )

    qs_parts = []
    for k in ("q", "category", "group"):
        v = request.args.get(k, "")
        if v:
            qs_parts.append(f"{k}={v}")
    query_string = "&".join(qs_parts)

    return render_template(
        "kb.html",
        articles     = [a.to_dict() for a in articles],
        total        = total,
        page         = page,
        pages        = pages,
        query_string = query_string,
        q=q, category=category, group=group,
        categories   = _kb_categories(),
        groups       = _kb_groups(),
    )


@ui_blueprint.get("/ui/kb/<string:sys_id>")
def kb_detail(sys_id):
    article = KBArticle.query.filter_by(sys_id=sys_id).first()
    if not article:
        abort(404)
    # Increment view count
    article.view_count = (article.view_count or 0) + 1
    db.session.commit()
    return render_template("kb_detail.html", article=article.to_dict())


# ── Helpers ───────────────────────────────────────────────────────────────────

def _incident_states():
    from sqlalchemy import distinct
    rows = db.session.query(distinct(Incident.state)).filter(Incident.state.isnot(None)).all()
    return sorted([r[0] for r in rows if r[0]])


def _group_names():
    rows = db.session.query(AssignmentGroup.name).order_by(AssignmentGroup.name).all()
    return [r[0] for r in rows]


def _kb_categories():
    from sqlalchemy import distinct
    rows = db.session.query(distinct(KBArticle.category)).filter(KBArticle.category.isnot(None)).all()
    return sorted([r[0] for r in rows if r[0]])


def _kb_groups():
    from sqlalchemy import distinct
    rows = db.session.query(distinct(KBArticle.assignment_group)).filter(KBArticle.assignment_group.isnot(None)).all()
    return sorted([r[0] for r in rows if r[0]])
