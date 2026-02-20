from datetime import datetime, timezone
from typing import Iterable, List

from fastapi import FastAPI

from api.foundation_models import (
    ApiFoundationDomainsResponse,
    ApiFoundationRoutesResponse,
    ApiFoundationStatusResponse,
    ApiRouteEntry,
)

FOUNDATION_DOMAINS = [
    "cyber",
    "security",
    "defense",
    "science",
    "military",
    "space",
    "engineering",
    "architecture",
]

FOUNDATION_CAPABILITIES = [
    "route-discovery",
    "status-introspection",
    "typed-api-contract",
    "domain-awareness",
]


class ApiFoundationService:
    def __init__(self, app: FastAPI) -> None:
        self._app = app

    def get_status(self) -> ApiFoundationStatusResponse:
        routes = self._collect_routes()
        return ApiFoundationStatusResponse(
            ok=True,
            service="swarmz",
            api_version="v1",
            generated_at=datetime.now(timezone.utc),
            route_count=len(routes),
            domains=FOUNDATION_DOMAINS,
            capabilities=FOUNDATION_CAPABILITIES,
        )

    def get_routes(self) -> ApiFoundationRoutesResponse:
        routes = self._collect_routes()
        return ApiFoundationRoutesResponse(
            ok=True,
            generated_at=datetime.now(timezone.utc),
            routes=routes,
        )

    def get_domains(self) -> ApiFoundationDomainsResponse:
        return ApiFoundationDomainsResponse(
            ok=True,
            generated_at=datetime.now(timezone.utc),
            domains=FOUNDATION_DOMAINS,
        )

    def _collect_routes(self) -> List[ApiRouteEntry]:
        entries: List[ApiRouteEntry] = []
        for route in self._app.routes:
            path = getattr(route, "path", None)
            methods: Iterable[str] = getattr(route, "methods", [])
            if not path or not isinstance(path, str):
                continue
            normalized_methods = sorted(
                [m for m in methods if m not in {"HEAD", "OPTIONS"}]
            )
            if not normalized_methods:
                continue
            entries.append(ApiRouteEntry(path=path, methods=normalized_methods))
        entries.sort(key=lambda item: item.path)
        return entries
