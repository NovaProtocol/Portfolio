from __future__ import annotations

from apps import create_app
from apps.config import config_dict

app = create_app(config_dict["Production"])
