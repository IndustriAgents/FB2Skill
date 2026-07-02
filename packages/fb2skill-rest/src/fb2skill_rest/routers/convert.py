from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from fb2skill_core.config import ONTOLOGIES, RenderConfig

from ..schemas.convert import ConvertResponse
from ..services.conversion import ConversionError, convert_zip

router = APIRouter(tags=["convert"])


@router.post("/convert", response_model=ConvertResponse)
async def convert(
    project_zip: UploadFile = File(..., description="IEC 61499 project as a zip archive"),
    endpoint_url: str = Form(...),
    base_iri: str = Form(...),
    resource: str = Form(...),
    namespace_index: int = Form(2),
    only: str = Form(""),
    opcua_xml_rel_path: str = Form(""),
    ontology: str = Form("maestro"),
) -> ConvertResponse:
    if ontology not in ONTOLOGIES:
        raise HTTPException(
            status_code=422,
            detail=f"unknown ontology {ontology!r}; expected one of {list(ONTOLOGIES)}",
        )
    only_tuple = tuple(s for s in only.split(",") if s)
    render_config = RenderConfig(
        endpoint_url=endpoint_url,
        base_iri=base_iri,
        resource=resource,
        namespace_index=namespace_index,
        only=only_tuple,
        ontology=ontology,
    )
    zip_bytes = await project_zip.read()
    try:
        return convert_zip(
            zip_bytes,
            render_config,
            opcua_xml_rel_path=opcua_xml_rel_path or None,
            source_zip_name=project_zip.filename or "project.zip",
        )
    except ConversionError as e:
        raise HTTPException(status_code=422, detail=str(e))
