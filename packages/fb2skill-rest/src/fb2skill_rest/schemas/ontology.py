from pydantic import BaseModel


class OntologyGroup(BaseModel):
    id: str
    label: str
    files: list[str]


class OntologyInfo(BaseModel):
    id: str
    label: str
    version: str
    license: str | None = None
    baseIri: str | None = None
    source: str | None = None
    groups: list[OntologyGroup]


class OntologiesResponse(BaseModel):
    ontologies: list[OntologyInfo]
