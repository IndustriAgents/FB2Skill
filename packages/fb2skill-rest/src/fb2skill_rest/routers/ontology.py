from pathlib import PurePosixPath

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..schemas.ontology import OntologiesResponse
from ..services.ontology import load_manifest, ontology_file_path, ontology_path

router = APIRouter(tags=["ontology"])


@router.get("/ontology")
def ontology() -> FileResponse:
    """Legacy single-file endpoint: the bundled CaSkMan ontology."""
    return FileResponse(
        ontology_path(),
        media_type="text/turtle",
        filename="CaSkMan_v4.3.0.ttl",
    )


@router.get("/ontologies", response_model=OntologiesResponse)
def ontologies() -> dict:
    """Manifest of every bundled target ontology and its files, grouped by module."""
    return load_manifest()


@router.get("/ontologies/{ontology_id}/files/{file_path:path}")
def ontology_file(ontology_id: str, file_path: str) -> FileResponse:
    try:
        path = ontology_file_path(ontology_id, file_path)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return FileResponse(
        path,
        media_type="text/turtle",
        filename=PurePosixPath(file_path).name,
    )
