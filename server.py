# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Thin entry-point shim for uvicorn / Railway.

All routes are registered inside swarmz_runtime.api.server.create_app().
This file exists solely to expose ``app`` for ``uvicorn server:app``.
"""

from swarmz_runtime.api.server import create_app  # noqa: F401

app = create_app()
