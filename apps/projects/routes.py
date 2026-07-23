from __future__ import annotations

from flask import abort, render_template

from apps.projects import blueprint

PROJECTS: dict[str, dict] = {
    "gatekeeper": {
        "title": "GateKeeper",
        "subtitle": "Access code auth gate for web apps",
        "description": (
            "A lightweight Flask-based authentication gateway that protects web apps "
            "behind access codes. Users log in with a code on the GateKeeper, receive "
            "a cross-subdomain cookie, and get redirected back. Protected apps verify "
            "sessions via an internal API endpoint. Uses signed cookies and short-lived "
            "tickets for stateless verification."
        ),
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
        "description": (
            "This site. A Flask-based portfolio that showcases projects and skills. "
            "Protected by GateKeeper — unauthenticated visitors are redirected to log in, "
            "then sent back with a verified session. Uses ProxyFix middleware to correctly "
            "handle HTTPS behind Cloudflare Tunnel."
        ),
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
            "A full-stack water utility billing management platform with NFC-enabled meter reading, 4 authentication systems, and automated payment reconciliation via Xendit. Built for a Philippine real estate developer serving residential tenants.",
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
