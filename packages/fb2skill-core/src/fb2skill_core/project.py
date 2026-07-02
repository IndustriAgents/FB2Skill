"""Walk an IEC 61499 project: find .fbt skill files + the deployment OPC UA XML."""
from pathlib import Path

from lxml import etree

from .fbt_parser import ParsedFbt, parse_fbt

_PARSER = etree.XMLParser(load_dtd=False, no_network=True, resolve_entities=False)


def discover_skill_fbts(project_root: Path) -> list[ParsedFbt]:
    """Recursively find every .fbt under ``project_root`` whose FBNetwork
    contains a ``<FB Type="BasicSKILL"/>`` and return the parsed objects."""
    skills: list[ParsedFbt] = []
    for fbt in sorted(project_root.rglob("*.fbt")):
        # Skip anything under build artifact folders.
        parts = {p.lower() for p in fbt.parts}
        if "bin" in parts or "obj" in parts:
            continue
        parsed = parse_fbt(fbt)
        if parsed is not None:
            skills.append(parsed)
    return skills


def find_deployment_opcua_xml(project_root: Path) -> Path | None:
    """Locate the auto-generated ``System.<resource>.opcua.xml`` under
    ``<project_root>/**/bin/Deploy/**/``. Returns the most recently modified
    match if several exist; ``None`` if nothing is found."""
    candidates = list(project_root.rglob("bin/Deploy/*/System.*.opcua.xml"))
    if not candidates:
        candidates = list(project_root.rglob("System.*.opcua.xml"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def build_instance_name_index(project_root: Path) -> dict[str, str]:
    """Map each FB type name to the instance name it's given wherever it's
    actually placed in the project: the Application FBNetwork (``*.sys``)
    and, for composite skills, the nested FBNetworks inside other ``*.fbt``
    files. The OPC UA deployment exposes objects by this instance name, not
    by the block's type name, so this bridges the two.
    """
    index: dict[str, str] = {}
    for pattern in ("*.sys", "*.fbt"):
        for path in sorted(project_root.rglob(pattern)):
            parts = {p.lower() for p in path.parts}
            if "bin" in parts or "obj" in parts:
                continue
            try:
                tree = etree.parse(str(path), parser=_PARSER)
            except etree.XMLSyntaxError:
                continue
            for fb in tree.getroot().iter("FB"):
                name, fb_type = fb.get("Name"), fb.get("Type")
                if name and fb_type and fb_type != "BasicSKILL" and fb_type not in index:
                    index[fb_type] = name
    return index
