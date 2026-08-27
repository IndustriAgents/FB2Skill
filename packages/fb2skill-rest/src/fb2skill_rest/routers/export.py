from fastapi import APIRouter, HTTPException, Response

from ..schemas.export import ExportSkillRequest, ExportZipRequest
from ..services.export import build_skills_zip, safe_filename

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/skill")
def export_skill(req: ExportSkillRequest) -> Response:
    """Return one rendered skill as a downloadable ``.ttl`` file."""
    filename = f"{safe_filename(req.name)}.ttl"
    return Response(
        content=req.ttl,
        media_type="text/turtle",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/skills.zip")
def export_skills_zip(req: ExportZipRequest) -> Response:
    """Return all rendered skills (plus optional ontology files) as one zip."""
    try:
        data = build_skills_zip(req.skills, req.include_ontology)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="skills.zip"'},
    )
