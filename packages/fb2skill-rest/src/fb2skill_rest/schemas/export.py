from pydantic import BaseModel, Field

from .convert import SkillTtl
from .graphdb import OntologyFileRef


class ExportSkillRequest(SkillTtl):
    pass


class ExportZipRequest(BaseModel):
    skills: list[SkillTtl] = Field(..., min_length=1)
    include_ontology: list[OntologyFileRef] = []
