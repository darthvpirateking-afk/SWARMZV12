# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""nexusmon/oig -- Operator Identity Graph (OIG) for NEXUSMON.

The OIG is the soul of NEXUSMON's bond with its operator.
It's a temporal knowledge graph that captures who the operator is,
how they've changed, and what NEXUSMON has learned about them.

Key components:
    models    -- Pydantic data models for all OIG entity types
    graph     -- SQLite-native temporal graph (bi-temporal edges)
    ingestion -- Conversation -> OIG ingestion pipeline
    retrieval -- Hybrid retrieval for context assembly
    routes    -- FastAPI REST routes (/v1/nexusmon/oig/*)
    mcp_server -- MCP server exposing NEXUSMON tools
"""
