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
        "url": "https://gatekeeper.projectnova.download/",
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
            "Live status indicators for project URLs",
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
        "description": (
            "A full-stack water utility billing management platform serving a Philippine "
            "real estate developer. Manages customer enrollment, NFC/QR meter readings, "
            "tiered billing computation, payment processing (GCash, Maya, cards), "
            "and a staff portal."
        ),
        "tech": {
            "web": ["Flask", "MySQL", "Docker", "Gunicorn", "Xendit API"],
            "mobile": ["React Native", "Expo", "NFC", "SQLite"],
        },
        "features": [
            "Customer enrollment with GPS mapping via Leaflet",
            "NFC tag & QR code meter reading with offline sync",
            "Tiered billing (5 tiers) with late penalties",
            "Online payments via Xendit gateway",
            "Staff portal with 7 role-based permissions",
            "Offline-capable mobile app (Expo/React Native)",
            "Change detection sync for mobile data",
        ],
        "url": "https://water-billing-system.ghoul-aldebaran.ts.net/",
        "github": "https://github.com/NovaProtocol/WaterBillingSystem",
        "image": "assets/images/water-billing-system/water-billing-system-preview.png",
        "links": [
            {"name": "Staff Site", "url": "https://water-billing-system.ghoul-aldebaran.ts.net/staff/", "icon": "fas fa-user-tie"},
            {"name": "Dev Site", "url": "https://water-billing-system.ghoul-aldebaran.ts.net/developer/", "icon": "fas fa-code-branch"},
            {"name": "Documentation", "url": "https://water-billing-system.ghoul-aldebaran.ts.net/documentation", "icon": "fas fa-book"},
        ],
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
