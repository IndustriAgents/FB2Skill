from fastapi import APIRouter, HTTPException, Response

from ..schemas.graphdb import (
    ConnectionRequest,
    ExportRequest,
    GraphListResponse,
    PushRequest,
    PushResponse,
    TestConnectionResponse,
)
from ..services import graphdb as svc

router = APIRouter(prefix="/graphdb", tags=["graphdb"])


@router.post("/test", response_model=TestConnectionResponse)
def test_connection(req: ConnectionRequest) -> dict:
    """Check reachability, credentials and repository health."""
    try:
        return svc.test_connection(req.connection)
    except svc.GraphDBServiceError as e:
        raise HTTPException(status_code=e.status, detail=e.detail)


@router.post("/graphs", response_model=GraphListResponse)
def list_graphs(req: ConnectionRequest) -> dict:
    """Named graphs present in the repository."""
    try:
        return {"graphs": svc.list_graphs(req.connection)}
    except svc.GraphDBServiceError as e:
        raise HTTPException(status_code=e.status, detail=e.detail)


@router.post("/push", response_model=PushResponse)
def push(req: PushRequest) -> dict:
    """Upload Turtle documents (skills or bundled ontology files) into GraphDB.

    Items are pushed independently; per-item failures are reported in the
    response. A failure of the connection itself is an HTTP error.
    """
    try:
        return {"results": svc.push_documents(req.connection, req.mode, req.items)}
    except svc.GraphDBServiceError as e:
        raise HTTPException(status_code=e.status, detail=e.detail)


@router.post("/export")
def export(req: ExportRequest) -> Response:
    """Download a named graph (or the whole repository) as Turtle."""
    try:
        ttl = svc.export_turtle(req.connection, req.graph, req.infer)
    except svc.GraphDBServiceError as e:
        raise HTTPException(status_code=e.status, detail=e.detail)
    filename = svc.export_filename(req.connection, req.graph)
    return Response(
        content=ttl,
        media_type="text/turtle",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
