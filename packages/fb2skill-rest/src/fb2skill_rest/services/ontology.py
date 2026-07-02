import json
from functools import lru_cache
from importlib.resources import as_file, files
from pathlib import Path

import fb2skill_core

_ONTOLOGY = "data/CaSkMan_v4.3.0.ttl"

# Synthesized entry for the single-file CaSkMan bundle; MAESTRO's entry is
# read from its bundled manifest.json.
_CASKMAN_MANIFEST = {
    "id": "caskman",
    "label": "CaSkMan",
    "version": "4.3.0",
    "license": None,
    "baseIri": "http://www.w3id.org/hsu-aut/caskman",
    "groups": [
        {"id": "ontology", "label": "Ontology", "files": ["CaSkMan_v4.3.0.ttl"]},
    ],
}

# ontology id -> data subdirectory holding its files.
_ONTOLOGY_DIRS = {"caskman": "data", "maestro": "data/maestro"}


def ontology_path() -> Path:
    """Return a filesystem Path to the bundled CaSkMan ontology.

    Works for both editable installs and built wheels. The resource is already
    a real file because fb2skill-core ships it via hatch force-include.
    """
    res = files(fb2skill_core).joinpath(_ONTOLOGY)
    with as_file(res) as p:
        return Path(p)


def _data_root(ontology_id: str) -> Path:
    res = files(fb2skill_core).joinpath(_ONTOLOGY_DIRS[ontology_id])
    with as_file(res) as p:
        return Path(p)


@lru_cache(maxsize=1)
def load_manifest() -> dict:
    """Combined manifest of every bundled ontology, keyed for the REST API."""
    maestro_json = files(fb2skill_core).joinpath("data/maestro/manifest.json")
    maestro = json.loads(maestro_json.read_text(encoding="utf-8"))
    # MAESTRO first: it is the default target ontology.
    return {"ontologies": [maestro, _CASKMAN_MANIFEST]}


def ontology_file_path(ontology_id: str, rel_path: str) -> Path:
    """Resolve one bundled ontology file, allowlisted against the manifest.

    Raises ``LookupError`` for an unknown ontology id or any path that is not
    listed in the manifest (which also rules out traversal — no path
    arithmetic is done on unvalidated input).
    """
    if ontology_id not in _ONTOLOGY_DIRS:
        raise LookupError(f"unknown ontology {ontology_id!r}")
    entry = next(
        o for o in load_manifest()["ontologies"] if o["id"] == ontology_id
    )
    allowed = {f for g in entry["groups"] for f in g["files"]}
    if rel_path not in allowed:
        raise LookupError(f"unknown ontology file {rel_path!r}")
    root = _data_root(ontology_id)
    resolved = (root / rel_path).resolve()
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        raise LookupError(f"unknown ontology file {rel_path!r}")
    return resolved
