# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Legacy entry point — delegates to swarmz_runtime.api.server.

Kept for backward compatibility with scripts that reference swarmz_server.
"""

from swarmz_runtime.api.server import create_app, app  # noqa: F401
