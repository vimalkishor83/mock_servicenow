"""KB Article service — mirrors ServiceNow kb_knowledge table behaviour."""

import logging
from models.db_models import KBArticle, db

log = logging.getLogger(__name__)


def _next_kb_number():
    """Generate the next KB article number like KB0001001."""
    from sqlalchemy import func
    import re
    max_num = db.session.query(func.max(KBArticle.number)).scalar()
    if not max_num:
        return "KB0001001"
    match = re.search(r"(\d+)$", max_num)
    next_val = int(match.group(1)) + 1 if match else 1001
    return f"KB{next_val:07d}"


class KBService:

    @staticmethod
    def list_articles(args):
        limit  = min(int(args.get("sysparm_limit", 100)), 10000)
        offset = max(int(args.get("sysparm_offset", 0)), 0)
        fields = KBService._parse_fields(args.get("sysparm_fields"))

        query = KBArticle.query

        # Support simple sysparm_query filters (active=true, assignment_group=X)
        raw_query = args.get("sysparm_query", "")
        if raw_query:
            query = KBService._apply_query(query, raw_query)

        articles = (
            query.order_by(KBArticle.view_count.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [a.to_dict(fields) for a in articles]

    @staticmethod
    def get_article(sys_id, fields=None):
        article = KBArticle.query.filter_by(sys_id=sys_id).first()
        if not article:
            return None
        return article.to_dict(KBService._parse_fields(fields))

    @staticmethod
    def create_article(data):
        article = KBArticle(
            number            = _next_kb_number(),
            short_description = data.get("short_description") or "Untitled KB Article",
            text              = data.get("text") or "",
            category          = data.get("category"),
            keywords          = data.get("keywords"),
            assignment_group  = data.get("assignment_group"),
            author            = data.get("author"),
            active            = str(data.get("active", "true")).lower() in {"true", "1", "yes"},
        )
        db.session.add(article)
        db.session.commit()
        log.info('KB article created: number=%s', article.number)
        return article.to_dict()

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_fields(raw):
        if not raw:
            return None
        return [f.strip() for f in raw.split(",") if f.strip()]

    @staticmethod
    def _apply_query(query, raw_query):
        """Apply simple field=value filters split by ^."""
        OPERATORS = [">=", "<=", "!=", ">", "<", "="]
        for clause in raw_query.split("^"):
            clause = clause.strip()
            for op in OPERATORS:
                if op in clause:
                    field, _, value = clause.partition(op)
                    field = field.strip()
                    value = value.strip()
                    column = getattr(KBArticle, field, None)
                    if column is None:
                        break
                    # Handle boolean active field
                    if field == "active":
                        value = value.lower() in {"true", "1", "yes"}
                    if op == "=":
                        query = query.filter(column == value)
                    elif op == "!=":
                        query = query.filter(column != value)
                    elif op == ">":
                        query = query.filter(column > value)
                    elif op == "<":
                        query = query.filter(column < value)
                    elif op == ">=":
                        query = query.filter(column >= value)
                    elif op == "<=":
                        query = query.filter(column <= value)
                    break
        return query
