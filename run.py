from __future__ import annotations

import os
import sys

from apps import create_app
from apps.config import config_dict

deployment_type = os.environ.get("DEPLOYMENT_TYPE")

if deployment_type not in ("DEBUG", "PRODUCTION"):
    print(
        "FATAL: DEPLOYMENT_TYPE must be DEBUG or PRODUCTION "
        "(set the environment variable before running).",
        file=sys.stderr,
    )
    sys.exit(1)

app = create_app(config_dict[deployment_type.capitalize()])
DEBUG = deployment_type == "DEBUG"

if __name__ == "__main__":
    if DEBUG:
        app.run(host="0.0.0.0", port=7010, debug=True)
    else:
        try:
            from gunicorn.app.base import BaseApplication
        except ImportError:
            print("gunicorn is not installed. Run: pip install gunicorn", file=sys.stderr)
            sys.exit(1)

        class StandaloneApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                for key, value in self.options.items():
                    self.cfg.set(key, value)

            def load(self):
                return self.application

        gunicorn_opts = {
            "bind": "0.0.0.0:7010",
            "worker_class": "gthread",
            "workers": 2,
            "threads": 4,
            "accesslog": "-",
            "loglevel": "info",
            "capture_output": True,
            "enable_stdio_inheritance": True,
        }
        StandaloneApplication(app, gunicorn_opts).run()
