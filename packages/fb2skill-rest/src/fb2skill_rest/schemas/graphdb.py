"""Request/response models for the GraphDB integration.

The connection details are supplied by the client on every request and are
never persisted or logged server-side.
"""

from typing import Literal

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator


class GraphDBConnection(BaseModel):
    base_url: str = Field(..., description="GraphDB server URL, e.g. http://localhost:7200")
    repository: str = Field(..., min_length=1, description="Repository id")
    username: str | None = None
    password: SecretStr | None = None
    timeout_s: int = Field(30, ge=1, le=600)

    @field_validator("base_url")
    @classmethod
    def _check_url(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v

    @property
    def auth(self) -> tuple[str, str] | None:
        if not self.username:
            return None
        pw = self.password.get_secret_value() if self.password else ""
        return (self.username, pw)


class ConnectionRequest(BaseModel):
    connection: GraphDBConnection


class RepositoryInfo(BaseModel):
    id: str
    title: str | None = None


class TestConnectionResponse(BaseModel):
    ok: bool
    protocol: str | None = None
    repository_found: bool = False
    repository_healthy: bool = False
    repositories: list[RepositoryInfo] = []
    message: str = ""


class GraphListResponse(BaseModel):
    graphs: list[str]


class OntologyFileRef(BaseModel):
    ontology_id: str
    file_path: str


class PushItem(BaseModel):
    name: str = Field(..., min_length=1)
    graph: str | None = Field(None, description="Named graph IRI; null/empty = default graph")
    ttl: str | None = None
    ontology_file: OntologyFileRef | None = None

    @model_validator(mode="after")
    def _one_source(self) -> "PushItem":
        if (self.ttl is None) == (self.ontology_file is None):
            raise ValueError("exactly one of 'ttl' or 'ontology_file' must be given")
        if self.graph is not None and not self.graph.strip():
            self.graph = None
        return self


class PushRequest(BaseModel):
    connection: GraphDBConnection
    mode: Literal["append", "replace"] = "append"
    items: list[PushItem] = Field(..., min_length=1)


class PushItemResult(BaseModel):
    name: str
    graph: str | None = None
    ok: bool
    triples: int | None = None
    error: str | None = None


class PushResponse(BaseModel):
    results: list[PushItemResult]


class ExportRequest(BaseModel):
    connection: GraphDBConnection
    graph: str | None = Field(None, description="Named graph IRI; null = whole repository")
    infer: bool = False

    @model_validator(mode="after")
    def _blank_graph(self) -> "ExportRequest":
        if self.graph is not None and not self.graph.strip():
            self.graph = None
        return self
