from __future__ import annotations

import os
import sys

from apps import create_app
from apps.config import config_dict

if __name__ == "__main__":
    mode = os.environ.get("DEPLOYMENT_TYPE", "").upper()
    if mode not in ("DEBUG", "PRODUCTION"):
        print(
            "FATAL: DEPLOYMENT_TYPE must be DEBUG or PRODUCTION "
            "(set the environment variable before running).",
            file=sys.stderr,
        )
        sys.exit(1)

    app = create_app(config_dict["Debug" if mode == "DEBUG" else "Production"])
    if mode == "DEBUG":
        app.run(host="0.0.0.0", port=7010, debug=True)
