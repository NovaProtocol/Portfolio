from __future__ import annotations

from apps import create_app
from apps.config import ProductionConfig

app = create_app(ProductionConfig)
