from __future__ import annotations

from markupsafe import Markup, escape

TAG_LINKS: dict[str, str] = {
    "Python": "https://www.python.org/",
    "C++": "https://isocpp.org/",
    "JavaScript": "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
    "Rust": "https://www.rust-lang.org/",
    "TypeScript": "https://www.typescriptlang.org/",
    "Flask": "https://flask.palletsprojects.com/",
    "FastAPI": "https://fastapi.tiangolo.com/",
    "Django": "https://www.djangoproject.com/",
    "SQLAlchemy": "https://www.sqlalchemy.org/",
    "MySQL": "https://www.mysql.com/",
    "SQLite": "https://www.sqlite.org/",
    "Jinja2": "https://jinja.palletsprojects.com/",
    "Node.js": "https://nodejs.org/",
    "Docker": "https://www.docker.com/",
    "Caddy": "https://caddyserver.com/",
    "Nginx": "https://nginx.org/",
    "Gunicorn": "https://gunicorn.org/",
    "Granian": "https://granian.dev/",
    "Debian": "https://www.debian.org/",
    "Bubblewrap": "https://github.com/containers/bubblewrap",
    "Cloudflare Tunnel": "https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/",
    "Tailscale Funnel": "https://tailscale.com/kb/1223/funnel/",
    "Bootstrap": "https://getbootstrap.com/",
    "Git": "https://git-scm.com/",
    "itsdangerous": "https://itsdangerous.palletsprojects.com/",
    "Xendit API": "https://www.xendit.co/",
    "NFC (NTAG215)": "https://www.nxp.com/products/rfid-nfc/ntag-for-tags-labels",
    "React Native": "https://reactnative.dev/",
    "Expo": "https://expo.dev/",
    "MathQuill": "https://mathquill.com/",
    "math.js": "https://mathjs.org/",
    "Arduino": "https://www.arduino.cc/",
    "ESP32": "https://www.espressif.com/",
    "ESP8266": "https://www.espressif.com/",
    "RP2040": "https://www.raspberrypi.com/products/rp2040/",
    "Raspberry Pi": "https://www.raspberrypi.com/",
    "STM32": "https://www.st.com/",
    "NTAG215": "https://www.nxp.com/products/rfid-nfc/ntag-for-tags-labels",
    "NTAG213": "https://www.nxp.com/products/rfid-nfc/ntag-for-tags-labels",
    "Mifare Classic 1K": "https://www.nxp.com/products/rfid-nfc/mifare-classic",
    "AutoCAD": "https://www.autodesk.com/products/autocad",
    "OnShape": "https://www.onshape.com/",
    "Fusion 360": "https://www.autodesk.com/products/fusion-360",
    "UltiMaker Cura": "https://ultimaker.com/software/ultimaker-cura",
}


def tech_tag(name: str) -> Markup:
    url = TAG_LINKS.get(name)
    if url:
        return Markup(
            f'<a class="tag" href="{escape(url)}" target="_blank" rel="noopener noreferrer">{escape(name)}</a>'
        )
    return Markup(f'<span class="tag">{escape(name)}</span>')


def init_app(app=None) -> None:
    # Legacy Flask helper. No-op on FastAPI. templating.py exposes tech_tag.
    try:
        app.jinja_env.globals["tech_tag"] = tech_tag  # type: ignore[attr-defined]
    except Exception:
        pass
