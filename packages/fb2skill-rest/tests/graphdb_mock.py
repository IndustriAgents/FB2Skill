"""In-memory fake of the GraphDB / RDF4J REST surface used by the service.

Built on ``httpx.MockTransport`` so the real ``GraphDBClient`` runs unchanged;
the transport is injected through ``fb2skill_rest.services.graphdb._transport_factory``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import httpx

CANNED_TTL = "@prefix ex: <http://example.org/> .\n\nex:s ex:p ex:o .\n"


@dataclass
class Recorded:
    method: str
    path: str
    params: dict[str, str]
    headers: dict[str, str]
    body: bytes


@dataclass
class FakeGraphDB:
    repositories: list[str] = field(default_factory=lambda: ["fb2skill"])
    graphs: list[str] = field(default_factory=lambda: ["urn:fb2skill:skill:skOld"])
    auth: tuple[str, str] | None = None  # when set, every request must carry basic auth
    unreachable: bool = False
    size: int = 3
    writes: list[Recorded] = field(default_factory=list)
    reads: list[Recorded] = field(default_factory=list)

    # -- helpers ---------------------------------------------------------
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handle)

    def _record(self, req: httpx.Request) -> Recorded:
        return Recorded(
            method=req.method,
            path=req.url.path,
            params=dict(req.url.params),
            headers={k.lower(): v for k, v in req.headers.items()},
            body=req.read(),
        )

    def _authorised(self, req: httpx.Request) -> bool:
        if self.auth is None:
            return True
        expected = httpx.BasicAuth(*self.auth)._auth_header  # noqa: SLF001
        return req.headers.get("authorization") == expected

    # -- router ----------------------------------------------------------
    def handle(self, req: httpx.Request) -> httpx.Response:
        if self.unreachable:
            raise httpx.ConnectError("connection refused", request=req)
        path = req.url.path
        if path == "/protocol":
            return httpx.Response(200, text="12")
        if not self._authorised(req):
            return httpx.Response(401, text="Unauthorized")
        if path == "/rest/repositories":
            body = [{"id": r, "title": f"{r} title", "type": "graphdb"} for r in self.repositories]
            return httpx.Response(200, json=body)

        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "repositories":
            repo = parts[1]
            if repo not in self.repositories:
                return httpx.Response(404, text=f"Unknown repository: {repo}")
            tail = parts[2:]
            if not tail:  # health probe: POST ASK {}
                return httpx.Response(
                    200, json={"head": {}, "boolean": True}
                )
            if tail == ["health"]:
                return httpx.Response(200, json={"status": "green"})
            if tail == ["size"]:
                return httpx.Response(200, text=str(self.size))
            if tail == ["contexts"]:
                body = {
                    "head": {"vars": ["contextID"]},
                    "results": {
                        "bindings": [
                            {"contextID": {"type": "uri", "value": g}} for g in self.graphs
                        ]
                    },
                }
                return httpx.Response(200, json=body)
            if tail == ["statements"]:
                rec = self._record(req)
                if req.method in ("POST", "PUT"):
                    self.writes.append(rec)
                    if b"BAD" in rec.body:
                        return httpx.Response(400, text="MALFORMED DATA: bad turtle")
                    return httpx.Response(204)
                if req.method == "GET":
                    self.reads.append(rec)
                    return httpx.Response(
                        200, text=CANNED_TTL, headers={"Content-Type": "text/turtle"}
                    )
        return httpx.Response(500, text=f"unhandled {req.method} {path} {json.dumps(dict(req.url.params))}")
