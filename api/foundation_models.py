from datetime import datetime
from typing import List

from pydantic import BaseModel


class ApiRouteEntry(BaseModel):
    path: str
    methods: List[str]


class ApiFoundationStatusResponse(BaseModel):
    ok: bool
    service: str
    api_version: str
    generated_at: datetime
    route_count: int
    domains: List[str]
    capabilities: List[str]


class ApiFoundationRoutesResponse(BaseModel):
    ok: bool
    generated_at: datetime
    routes: List[ApiRouteEntry]


class ApiFoundationDomainsResponse(BaseModel):
    ok: bool
    generated_at: datetime
    domains: List[str]
