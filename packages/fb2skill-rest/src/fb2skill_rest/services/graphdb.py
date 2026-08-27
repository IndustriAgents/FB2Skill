"""GraphDB integration.

This is the only module that talks to GraphDB. It uses the first-party
``rdflib.contrib.graphdb`` client for construction (auth, protocol check) and
the RDF4J REST protocol directly for statement upload / export so that Turtle
can be written to and read from arbitrary named graphs.

Connection details come from the request and are never stored.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager

import httpx
from rdflib import URIRef
from rdflib.contrib.graphdb import GraphDBClient
from rdflib.contrib.graphdb import exceptions as gdb_exc
from rdflib.contrib.rdf4j import exceptions as rdf4j_exc
from rdflib.contrib.rdf4j.client import Repository

from ..schemas.graphdb import GraphDBConnection, PushItem, PushItemResult, RepositoryInfo
from .ontology import ontology_file_path

TURTLE = "text/turtle"

# Test hook: return an httpx transport to inject into the client, or None.
_transport_factory: Callable[[], httpx.BaseTransport | None] = lambda: None


class GraphDBServiceError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def _truncate(text: str, n: int = 500) -> str:
    text = text.strip()
    return text if len(text) <= n else text[:n] + "..."


def _map_error(err: Exception, conn: GraphDBConnection) -> GraphDBServiceError:
    if isinstance(err, GraphDBServiceError):
        return err
    if isinstance(err, gdb_exc.UnauthorisedError):
        return GraphDBServiceError(401, "GraphDB rejected credentials")
    if isinstance(err, gdb_exc.ForbiddenError):
        return GraphDBServiceError(
            403, f"GraphDB: insufficient permissions for repository {conn.repository!r}"
        )
    if isinstance(err, rdf4j_exc.RepositoryNotFoundError):
        return GraphDBServiceError(404, f"Repository {conn.repository!r} not found")
    if isinstance(err, rdf4j_exc.RepositoryNotHealthyError):
        return GraphDBServiceError(503, str(err))
    if isinstance(err, gdb_exc.BadRequestError):
        return GraphDBServiceError(422, f"GraphDB rejected request: {_truncate(str(err))}")
    if isinstance(err, httpx.HTTPStatusError):
        code = err.response.status_code
        body = _truncate(err.response.text)
        if code == 401:
            return GraphDBServiceError(401, "GraphDB rejected credentials")
        if code == 403:
            return GraphDBServiceError(
                403, f"GraphDB: insufficient permissions for repository {conn.repository!r}"
            )
        if code == 404:
            return GraphDBServiceError(404, f"Repository {conn.repository!r} not found")
        if code == 400:
            return GraphDBServiceError(422, f"GraphDB rejected Turtle: {body}")
        return GraphDBServiceError(502, f"GraphDB returned {code}: {body}")
    if isinstance(err, (rdf4j_exc.RDF4JUnsupportedProtocolError, httpx.RequestError)):
        return GraphDBServiceError(502, f"Cannot reach GraphDB at {conn.base_url}: {err}")
    return GraphDBServiceError(502, f"GraphDB error: {err}")


@contextmanager
def open_client(conn: GraphDBConnection) -> Iterator[GraphDBClient]:
    kwargs: dict = {}
    transport = _transport_factory()
    if transport is not None:
        kwargs["transport"] = transport
    try:
        client = GraphDBClient(
            conn.base_url, auth=conn.auth, timeout=float(conn.timeout_s), **kwargs
        )
    except Exception as e:  # noqa: BLE001 - mapped below
        raise _map_error(e, conn) from e
    try:
        yield client
    except Exception as e:  # noqa: BLE001
        raise _map_error(e, conn) from e
    finally:
        client.close()


def _context_param(graph: str | None) -> dict[str, str]:
    """RDF4J ``context`` query parameter for a named graph (omitted = all/default)."""
    return {"context": URIRef(graph).n3()} if graph else {}


def _probe_repository(client: GraphDBClient, conn: GraphDBConnection) -> Repository:
    """Run ``ASK {}`` against the repository.

    Raises ``httpx.HTTPStatusError`` for any failure so that 401/403/404 are
    mapped by ``_map_error`` (the rdflib health check folds 401 into
    "not healthy", which would hide bad credentials).
    """
    resp = client.http_client.post(
        f"/repositories/{conn.repository}",
        headers={"Content-Type": "application/sparql-query", "Accept": "application/sparql-results+json"},
        content="ASK {}",
    )
    resp.raise_for_status()
    return Repository(conn.repository, client.http_client)


def test_connection(conn: GraphDBConnection) -> dict:
    with open_client(conn) as client:
        protocol = str(client.protocol)
        repositories: list[RepositoryInfo] = []
        try:
            for r in client.graphdb_repositories.list():
                if r.id:
                    repositories.append(RepositoryInfo(id=r.id, title=r.title))
        except Exception:  # noqa: BLE001 - listing is best effort
            repositories = []
        try:
            _probe_repository(client, conn)
            found, healthy = True, True
            message = f"Connected to repository {conn.repository!r}"
        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            if code in (401, 403):
                raise
            found = code != 404
            healthy = False
            message = (
                f"Repository {conn.repository!r} not found"
                if code == 404
                else f"Repository {conn.repository!r} is not healthy: {code} {_truncate(e.response.text)}"
            )
        return {
            "ok": found and healthy,
            "protocol": protocol,
            "repository_found": found,
            "repository_healthy": healthy,
            "repositories": repositories,
            "message": message,
        }


def list_graphs(conn: GraphDBConnection) -> list[str]:
    with open_client(conn) as client:
        repo = _probe_repository(client, conn)
        return [str(g) for g in repo.graph_names()]


def _resolve_ttl(item: PushItem) -> bytes:
    if item.ttl is not None:
        return item.ttl.encode("utf-8")
    ref = item.ontology_file
    assert ref is not None
    return ontology_file_path(ref.ontology_id, ref.file_path).read_bytes()


def push_documents(
    conn: GraphDBConnection, mode: str, items: list[PushItem]
) -> list[PushItemResult]:
    results: list[PushItemResult] = []
    with open_client(conn) as client:
        # Fail fast (mapped to 404/401/...) if the repository itself is unusable.
        repo = _probe_repository(client, conn)
        http = client.http_client
        url = f"/repositories/{conn.repository}/statements"
        headers = {"Content-Type": TURTLE}
        for item in items:
            try:
                payload = _resolve_ttl(item)
            except LookupError as e:
                results.append(
                    PushItemResult(name=item.name, graph=item.graph, ok=False, error=str(e))
                )
                continue
            try:
                params = _context_param(item.graph)
                if mode == "replace":
                    if not item.graph:
                        params = {"context": "null"}
                    resp = http.put(url, params=params, headers=headers, content=payload)
                else:
                    resp = http.post(url, params=params, headers=headers, content=payload)
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403, 404):
                    raise
                results.append(
                    PushItemResult(
                        name=item.name,
                        graph=item.graph,
                        ok=False,
                        error=_map_error(e, conn).detail,
                    )
                )
                continue
            triples: int | None
            try:
                triples = repo.size(URIRef(item.graph)) if item.graph else repo.size()
            except Exception:  # noqa: BLE001 - size is informational only
                triples = None
            results.append(
                PushItemResult(name=item.name, graph=item.graph, ok=True, triples=triples)
            )
    return results


def export_turtle(conn: GraphDBConnection, graph: str | None, infer: bool = False) -> str:
    with open_client(conn) as client:
        _probe_repository(client, conn)
        params = {"infer": "true" if infer else "false", **_context_param(graph)}
        resp = client.http_client.get(
            f"/repositories/{conn.repository}/statements",
            params=params,
            headers={"Accept": TURTLE},
        )
        resp.raise_for_status()
        return resp.text


def export_filename(conn: GraphDBConnection, graph: str | None) -> str:
    base = re.sub(r"[^A-Za-z0-9_.-]+", "_", conn.repository)
    if graph:
        slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", graph).strip("_")[:80]
        base = f"{base}-{slug}"
    return f"{base}.ttl"
