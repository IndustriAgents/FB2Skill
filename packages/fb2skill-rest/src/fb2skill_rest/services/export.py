"""Server-side download helpers for generated skill TTL."""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import PurePosixPath

from ..schemas.convert import SkillTtl
from ..schemas.graphdb import OntologyFileRef
from .ontology import ontology_file_path


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._")
    return cleaned or "skill"


def _unique(names: set[str], candidate: str) -> str:
    if candidate not in names:
        names.add(candidate)
        return candidate
    stem, dot, ext = candidate.rpartition(".")
    if not dot:
        stem, ext = candidate, ""
    n = 2
    while f"{stem}_{n}{dot}{ext}" in names:
        n += 1
    result = f"{stem}_{n}{dot}{ext}"
    names.add(result)
    return result


def build_skills_zip(skills: list[SkillTtl], ontology_refs: list[OntologyFileRef]) -> bytes:
    """Zip skills under ``skills/<name>.ttl`` and bundled ontology files under ``ontology/``.

    Raises ``LookupError`` for an unknown ontology file reference.
    """
    buf = io.BytesIO()
    seen: set[str] = set()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for s in skills:
            arc = _unique(seen, f"skills/{safe_filename(s.name)}.ttl")
            zf.writestr(arc, s.ttl)
        for ref in ontology_refs:
            path = ontology_file_path(ref.ontology_id, ref.file_path)
            arc = _unique(seen, f"ontology/{PurePosixPath(ref.file_path).name}")
            zf.write(path, arc)
    return buf.getvalue()
