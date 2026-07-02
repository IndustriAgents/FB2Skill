"""Render-time configuration shared by all fb2skill-core consumers.

CLI-only concerns (out_dir, verify, project_root, opcua_xml) live in
``fb2skill_cli.config.CliConfig``; this dataclass holds only the fields a
template needs to render a TTL.
"""
from dataclasses import dataclass

# Target ontology vocabularies a skill can be rendered into. Each id has a
# matching template set under ``templates/<id>/skill.ttl.j2``.
ONTOLOGIES: tuple[str, ...] = ("caskman", "maestro")


@dataclass(frozen=True)
class RenderConfig:
    endpoint_url: str
    base_iri: str
    resource: str
    namespace_index: int = 2
    # Provenance metadata for the header template. CLI passes
    # ``str(project_root)`` / ``opcua_xml.name``; REST passes the upload
    # filename / detected XML basename.
    project_label: str = ""
    source_label: str = ""
    only: tuple[str, ...] = ()
    # Target ontology vocabulary; selects the Jinja template set.
    ontology: str = "maestro"

    def __post_init__(self) -> None:
        if self.ontology not in ONTOLOGIES:
            raise ValueError(
                f"unknown ontology {self.ontology!r}; expected one of {ONTOLOGIES}"
            )
