from __future__ import annotations

from flask import abort, render_template

from apps.projects import blueprint

PROJECTS: dict[str, dict] = {
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
