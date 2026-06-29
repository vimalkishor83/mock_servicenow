import random
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from config import (  # noqa: E402
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    DUMMY_GROUP_COUNT,
    DUMMY_INCIDENT_COUNT,
    DUMMY_USER_COUNT,
)
from models.db_models import AssignmentGroup, Incident, KBArticle, User, db  # noqa: E402
from services.incident_service import IncidentService  # noqa: E402
from services.kb_service import KBService  # noqa: E402


GROUP_NAMES = [
    "Database Team",
    "Network Team",
    "Application Support",
    "Security Operations",
    "Cloud Platform",
    "Service Desk",
    "ERP Support",
    "Integration Team",
    "Storage Team",
    "Middleware Team",
]


def ensure_admin():
    admin = User.query.filter_by(user_name=DEFAULT_ADMIN_USERNAME).first()
    if admin:
        return admin
    admin = User(
        user_name=DEFAULT_ADMIN_USERNAME,
        name="System Administrator",
        email="admin@example.com",
        active=True,
        department="IT",
        title="Administrator",
    )
    admin.set_password(DEFAULT_ADMIN_PASSWORD)
    db.session.add(admin)
    db.session.commit()
    return admin


def seed_groups(count=DUMMY_GROUP_COUNT):
    for name in GROUP_NAMES[:count]:
        if not AssignmentGroup.query.filter_by(name=name).first():
            db.session.add(
                AssignmentGroup(
                    name=name,
                    description=f"{name} assignment group",
                    active=True,
                )
            )
    db.session.commit()


def seed_users(count=DUMMY_USER_COUNT):
    first_names = ["Avery", "Jordan", "Taylor", "Riley", "Morgan", "Casey", "Quinn", "Reese"]
    last_names = ["Patel", "Smith", "Johnson", "Chen", "Garcia", "Brown", "Singh", "Miller"]
    departments = ["IT", "Finance", "Operations", "Sales", "HR", "Engineering"]
    titles = ["Analyst", "Manager", "Engineer", "Specialist", "Coordinator"]

    existing = User.query.count()
    for index in range(existing, count + 1):
        username = f"user{index:03d}"
        if User.query.filter_by(user_name=username).first():
            continue
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        user = User(
            user_name=username,
            name=name,
            email=f"{username}@example.com",
            active=True,
            department=random.choice(departments),
            title=random.choice(titles),
        )
        user.set_password("Password123!")
        db.session.add(user)
    db.session.commit()


def seed_incidents(count=DUMMY_INCIDENT_COUNT):
    existing = Incident.query.count()
    for _ in range(max(count - existing, 0)):
        IncidentService.create_random_incident()


# KB articles that map to the incident themes used by mock incidents
KB_ARTICLES = [
    {
        "short_description": "Database listener down — ORA-12541 resolution",
        "text": (
            "Symptom: Application cannot connect to Oracle DB. Error ORA-12541 TNS No Listener.\n"
            "Root Cause: Oracle listener service stopped or misconfigured tnsnames.ora.\n"
            "Resolution:\n"
            "1. SSH to the DB server.\n"
            "2. Run: lsnrctl status\n"
            "3. If stopped: lsnrctl start\n"
            "4. Verify tnsnames.ora points to correct host/port.\n"
            "5. Restart the application connection pool."
        ),
        "category": "database",
        "keywords": "oracle listener ORA-12541 TNS database connectivity",
        "assignment_group": "Database Team",
    },
    {
        "short_description": "Disk space threshold exceeded — cleanup procedure",
        "text": (
            "Symptom: Alerts firing for disk usage above 85%.\n"
            "Root Cause: Log files or temp files accumulating without rotation.\n"
            "Resolution:\n"
            "1. Identify large files: du -sh /* | sort -rh | head -20\n"
            "2. Rotate and compress logs: logrotate -f /etc/logrotate.conf\n"
            "3. Clear /tmp: find /tmp -mtime +7 -delete\n"
            "4. Archive old application logs to NAS storage.\n"
            "5. Set up cron job for automated log rotation."
        ),
        "category": "storage",
        "keywords": "disk space full logs cleanup rotation storage",
        "assignment_group": "Application Support",
    },
    {
        "short_description": "External API returned HTTP 500 errors — debugging guide",
        "text": (
            "Symptom: Integration calls to external API returning 500 errors.\n"
            "Root Cause: External service degradation or breaking change in API contract.\n"
            "Resolution:\n"
            "1. Check external API status page / vendor communication.\n"
            "2. Review request/response logs in Splunk for error payload.\n"
            "3. Validate API endpoint URL, headers, and auth token validity.\n"
            "4. Enable circuit breaker pattern to prevent cascade failures.\n"
            "5. Raise P1 ticket with vendor if outage exceeds 30 minutes."
        ),
        "category": "api",
        "keywords": "API 500 external integration HTTP error connectivity",
        "assignment_group": "Integration Team",
    },
    {
        "short_description": "JVM OutOfMemoryError — heap dump analysis and fix",
        "text": (
            "Symptom: Application process crashes with java.lang.OutOfMemoryError: Java heap space.\n"
            "Root Cause: Memory leak in application or heap too small for workload.\n"
            "Resolution:\n"
            "1. Capture heap dump: jmap -dump:live,format=b,file=heap.hprof <pid>\n"
            "2. Analyse with Eclipse MAT or VisualVM — look for largest retained objects.\n"
            "3. Increase Xmx as immediate relief: -Xmx4g in JVM_OPTS.\n"
            "4. Fix the leak (common cause: cached collections growing unbounded).\n"
            "5. Set up JVM GC logging and memory alerts."
        ),
        "category": "performance",
        "keywords": "OutOfMemoryError JVM heap memory leak java performance",
        "assignment_group": "Application Support",
    },
    {
        "short_description": "Repeated login failures — account lockout and AD sync",
        "text": (
            "Symptom: Users reporting locked accounts after correct password entry.\n"
            "Root Cause: Stale Kerberos tickets or AD replication lag between DCs.\n"
            "Resolution:\n"
            "1. Unlock user account: Unlock-ADAccount -Identity <username>\n"
            "2. Force AD replication: repadmin /syncall /AdeP\n"
            "3. Clear Kerberos tickets on affected client: klist purge\n"
            "4. Check for service accounts using old passwords in Task Scheduler.\n"
            "5. Review failed login event IDs 4625 in Windows Security log."
        ),
        "category": "authentication",
        "keywords": "login failure locked account AD kerberos authentication",
        "assignment_group": "Security Operations",
    },
    {
        "short_description": "Network packet loss on core switch — remediation steps",
        "text": (
            "Symptom: Intermittent connectivity, high latency (>100ms), packet loss >1%.\n"
            "Root Cause: Duplex mismatch, faulty SFP transceiver, or spanning-tree instability.\n"
            "Resolution:\n"
            "1. Identify affected interface: show interface counters errors\n"
            "2. Check for duplex mismatch: show interface GigX/X\n"
            "3. Replace faulty SFP if CRC errors present.\n"
            "4. Verify spanning-tree topology: show spanning-tree detail\n"
            "5. Escalate to Network Team if physical layer issue confirmed."
        ),
        "category": "latency",
        "keywords": "network packet loss latency duplex SFP connectivity",
        "assignment_group": "Network Team",
    },
    {
        "short_description": "Nightly batch job failure — ETL error handling",
        "text": (
            "Symptom: Batch ETL job fails at 02:00 with FileNotFoundException or DB timeout.\n"
            "Root Cause: Source file not delivered on time or DB connection pool exhausted.\n"
            "Resolution:\n"
            "1. Check if source file arrived: ls -la /data/incoming/ | grep $(date +%Y%m%d)\n"
            "2. Re-trigger manually: ./run_etl.sh --date $(date +%Y-%m-%d) --force\n"
            "3. Increase DB connection pool max in application.properties.\n"
            "4. Add retry logic with exponential backoff to ETL job.\n"
            "5. Set up file arrival monitoring alert with 30-min pre-run warning."
        ),
        "category": "batch",
        "keywords": "batch ETL nightly job failure file database timeout",
        "assignment_group": "Application Support",
    },
    {
        "short_description": "Application process crashed — core dump analysis",
        "text": (
            "Symptom: Application process exits unexpectedly with exit code non-zero.\n"
            "Root Cause: Segmentation fault, uncaught exception, or OOM kill.\n"
            "Resolution:\n"
            "1. Check system journal: journalctl -xe -u <service-name>\n"
            "2. Check OOM killer: dmesg | grep -i 'killed process'\n"
            "3. If OOM killed: increase container memory limit or fix memory leak.\n"
            "4. If SIGSEGV: collect core dump and send to vendor.\n"
            "5. Enable automatic restart: systemctl enable --now <service>.service"
        ),
        "category": "runtime",
        "keywords": "process crash core dump OOM killed segfault application",
        "assignment_group": "Application Support",
    },
    {
        "short_description": "SSL certificate expiry causing HTTPS failures",
        "text": (
            "Symptom: Browser shows 'Certificate expired' or API calls fail with SSL handshake error.\n"
            "Root Cause: TLS certificate passed its Not After date.\n"
            "Resolution:\n"
            "1. Check expiry: openssl x509 -enddate -noout -in /etc/ssl/cert.pem\n"
            "2. Request new cert from CA or Let's Encrypt: certbot renew\n"
            "3. Install new cert and restart web server: systemctl reload nginx\n"
            "4. Verify: curl -vI https://yourdomain.com 2>&1 | grep 'expire'\n"
            "5. Add calendar reminder 30 days before next expiry."
        ),
        "category": "security",
        "keywords": "SSL TLS certificate expired HTTPS handshake error",
        "assignment_group": "Security Operations",
    },
    {
        "short_description": "ERP interface data sync failure — IDM mismatch",
        "text": (
            "Symptom: ERP and downstream system showing different record counts / stale data.\n"
            "Root Cause: Message queue backed up or interface record transformation error.\n"
            "Resolution:\n"
            "1. Check MQ queue depth: mqstat -m QMGR -q INTERFACE.IN\n"
            "2. Review interface log for transformation errors.\n"
            "3. Re-process failed messages from dead-letter queue.\n"
            "4. Verify IDM field mappings match current ERP schema.\n"
            "5. Trigger full reconciliation job if delta sync not viable."
        ),
        "category": "integration",
        "keywords": "ERP interface sync IDM message queue data mismatch",
        "assignment_group": "ERP Support",
    },
]


def seed_kb_articles():
    """Insert KB articles if not already present (idempotent)."""
    for article_data in KB_ARTICLES:
        title = article_data["short_description"]
        if not KBArticle.query.filter_by(short_description=title).first():
            KBService.create_article(article_data)


def seed_all(app=None):
    if app is None:
        from app import create_app

        app = create_app(start_background_jobs=False)
    with app.app_context():
        db.create_all()
        ensure_admin()
        seed_groups()
        seed_users()
        seed_incidents()
        seed_kb_articles()


if __name__ == "__main__":
    seed_all()
    print("Dummy data generated successfully.")
