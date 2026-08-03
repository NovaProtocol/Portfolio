from __future__ import annotations

from flask import abort, render_template

from apps.projects import blueprint

PROJECTS: dict[str, dict] = {
    "gatekeeper": {
        "title": "GateKeeper",
        "subtitle": "Access code auth gate for web apps",
        "description": [
            "A lightweight Flask-based authentication gateway that protects a family of web apps behind a single shared access-code system. Instead of user accounts, visitors prove access once by entering a code on the GateKeeper login page; the service hands back a signed, cross-subdomain cookie and a short-lived verification ticket, then redirects them to wherever they were going. One login covers every subdomain of the same apex domain — the portfolio, staff portals, the solver, and any future app — with no hardcoded domains anywhere in the stack.",
            "Protected apps never trust the cookie blindly: they verify it against the GateKeeper's internal API over the Docker network, receive a signed ticket (5-minute validity, verified locally with the shared secret), and cache the result, so the central service is only hit once per 5-minute window per user. Cookies are tamper-evident itsdangerous-signed values with no expiry — revoking a code in the admin panel is the kill switch, propagating within at most 5 minutes through ticket expiry. A password-protected admin panel manages the codes: 64-bit random generation, usage telemetry (last-accessed tracking), soft revocation that keeps an audit trail, a hide-inactive toggle, and a backup-code fallback so the owner is never locked out.",
        ],
        "tech": {
            "web": ["Flask", "SQLite", "Docker", "itsdangerous", "Cloudflare Tunnel"],
        },
        "features": [
            "Access code authentication with signed cookies",
            "Short-lived ticket-based session verification (5-min TTL)",
            "Cross-subdomain cookie for shared auth across apps",
            "Admin panel to create and revoke access codes",
            "Backup code fallback for emergency access",
            "REST API for integration with protected apps",
        ],
        "github": "https://github.com/NovaProtocol/GateKeeper",
        "links": [],
        "buttons": [],
    },
    "portfolio": {
        "title": "Portfolio",
        "subtitle": "Personal portfolio site",
        "description": [
            "This site. A Flask portfolio that documents every project in the stack, each with a detail page, tech tags, a live-site embed with online/offline status, and key features. Served by Gunicorn inside a Docker container and exposed through a Cloudflare tunnel, with ProxyFix middleware so HTTPS and forwarded headers behave correctly behind the tunnel.",
            "It doubles as the integration test for the rest of the ecosystem: protected by GateKeeper, so unauthenticated visitors are redirected to log in and sent back with a verified session; project pages embed the other live apps directly — solving problems in the sandbox, browsing bills, or managing access codes without leaving the page.",
        ],
        "tech": {
            "web": ["Flask", "Gunicorn", "Docker", "Cloudflare Tunnel"],
        },
        "features": [
            "Project showcase with detail pages and tech tags",
            "GateKeeper integration for access control",
            "ProxyFix middleware for correct HTTPS behind tunnel",
        ],
        "url": "https://portfolio.projectnova.download/",
        "github": "https://github.com/NovaProtocol/Portfolio",
        "links": [],
        "buttons": [],
    },
    "water-billing-system": {
        "title": "Water Billing System",
        "subtitle": "Cotta Realty & Development Corporation",
        "description": [
            "A full-stack water utility billing management platform with NFC-enabled meter reading, 4 authentication systems, and automated payment reconciliation via Xendit. Built for Cotta Realty & Development Corporation, serving residential tenants across multiple subdivisions in Quezon, Philippines.",
            "A React Native field app gives meter readers an offline-first workflow: customer lists, reading history, and NFC tag data are downloaded during sync, and readings are queued in local SQLite until connectivity returns. Meter tags are NTAG215 NFC chips whose passwords are derived on-device from the tag's unclonable factory UID using SHA-256 — the secret never touches the server or the network — with tamper detection, on-device enrollment with read-back verification of every write, and duplicate-month protection enforced both locally and server-side.",
            "Readings auto-generate bills against a 5-tier progressive water tariff with late penalties. Payments use a waterfall model: money settles the oldest unpaid bill first, excess rolls over as credit, and a single receipt can span multiple bills with receipt-group undo. 22 payment methods (GCash, Maya, cards, bank debits, over-the-counter, QRPh) each carry their own fee structure, and online payments flow through Xendit payment sessions.",
            "Online payments are reconciled through two paths: an instant webhook auto-pays the moment Xendit confirms, and a self-rescheduling background worker re-checks stuck transactions every 5 minutes and can reverse payments Xendit later reverses. The platform runs as 11 Docker containers behind a Caddy reverse proxy with 6 networks — the API is unreachable from the edge, portals reach it only over an internal network, and phpMyAdmin and documentation sit on a private port behind GateKeeper SSO.",
            "Project Note: This project is hosted on a low-end server and thus, does not represent the full expected performance of the system. It is only a demo version meant to showcase the features and functionality.",
        ],
        "tech": {
            "web": ["Flask", "SQLAlchemy", "MySQL 8.4", "Caddy", "Gunicorn", "Xendit API", "Cloudflare Tunnel", "Docker"],
            "mobile": ["React Native", "Expo", "TypeScript", "NFC (NTAG215)", "SQLite"],
        },
        "features": [
            "11 Docker containers with 6 internal networks (public/private/API isolation)",
            "Caddy reverse proxy separating public (:7020) and private (:7021) traffic",
            "4 authentication systems: API keys, Flask-Login, signed cookies, GateKeeper SSO",
            "NFC tag reading (NTAG215 PWD_AUTH) with offline-capable React Native app",
            "DB-backed background task queue with Xendit payment reconciliation",
            "MkDocs documentation site with full API reference and architecture docs",
            "phpMyAdmin admin interface proxied through Caddy on private port",
        ],
        "url": "https://water-billing-system.projectnova.download/",
        "github": "https://github.com/NovaProtocol/WaterBillingSystem",
        "image": "assets/images/water-billing-system/water-billing-system-preview.png",
        "links": [
            {"name": "Staff Site", "url": "https://water-billing-system-private.projectnova.download/staff/", "icon": "fas fa-user-tie"},
            {"name": "Dev Site", "url": "https://water-billing-system-private.projectnova.download/developer/", "icon": "fas fa-code-branch"},
            {"name": "Documentation", "url": "https://water-billing-system-private.projectnova.download/documentation/", "icon": "fas fa-book"},
        ],
        "testing": {
            "staff": {
                "username": "superuser",
                "password": "superuser",
            },
            "customer": {
                "account_number": "1 to 10000",
                "registered_name": "Not needed (DEBUG mode)",
                "last_receipt_number": "Not needed (DEBUG mode)",
            },
        },
        "buttons": [],
    },
    "solvespace": {
        "title": "SolveSpace",
        "subtitle": "Self-hosted Python practice sandbox",
        "description": [
            "A self-hosted platform for practicing Python programming problems. A Flask frontend, protected by GateKeeper auth, offers a browsable problem library with images, tags, and per-problem progress tracking, plus a code submission interface. Problems and submissions are stored in MySQL, and a separate executor container picks up submissions from a queue and runs them in a hardened bubblewrap sandbox — the web app and the code runner never share a process.",
            "Every submission executes in its own sandbox. Bubblewrap gives it a private set of namespaces (user, network, IPC, PID, UTS, cgroup, time), so it has no network access and cannot see other processes. The system is read-only: only /usr, /usr/local, /lib, and /lib64 are bound in, /tmp is a RAM-backed tmpfs that vanishes when the process dies, and /dev is freshly populated. The environment is completely empty — no variables, no secrets, nothing inherited from the host. Hard resource limits are enforced on the entire process tree before the code starts: 1GB of address space, 64 processes, 25 CPU seconds, and core dumps disabled — and user code cannot raise any of them.",
            "There is no fallback path: if the sandbox fails to start, the submission is marked failed rather than ever running unsandboxed. Every case is judged against hidden expected outputs with per-case pass/fail results, timing, and peak memory tracked. The executor container itself is capped at 1GB of RAM, 2 CPUs, and 128 processes, keeping it fully isolated from the database and web app.",
        ],
        "tech": {
            "web": ["Flask", "Gunicorn", "MySQL 8.4", "Docker", "Bubblewrap", "Cloudflare Tunnel"],
        },
        "features": [
            "Problem library with images, tags, and hidden judge test cases",
            "Sandboxed solution judging via bubblewrap with hard rlimits (1GB memory, 25s CPU, 64 processes)",
            "Background execution queue in MySQL, polled by a dedicated executor container",
            "GateKeeper-protected frontend with per-problem progress tracking",
            "phpMyAdmin for database management",
        ],
        "url": "https://solver.projectnova.download/",
        "github": "https://github.com/NovaProtocol/SolveSpace",
        "links": [],
        "buttons": [],
    },
}


def sorted_projects() -> list[tuple[str, dict]]:
    return sorted(PROJECTS.items(), key=lambda item: item[1]["title"])


@blueprint.route("/")
def index():
    return render_template("projects/index.html", projects=sorted_projects())


@blueprint.route("/info/<slug>/")
def detail(slug: str):
    project = PROJECTS.get(slug)
    if not project:
        abort(404)
    return render_template("projects/detail.html", project=project, slug=slug)
