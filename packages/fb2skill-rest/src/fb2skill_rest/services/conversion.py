"""Zip-upload -> TTL pipeline. The only place that wires fb2skill-core to HTTP."""
from __future__ import annotations

import dataclasses
import tempfile
import zipfile
from pathlib import Path

from fb2skill_core.config import RenderConfig
from fb2skill_core.opcua_nodes import (
    SkillResolutionError,
    load_node_set,
    resolve_bindings,
)
from fb2skill_core.project import (
    build_instance_name_index,
    discover_skill_fbts,
    find_deployment_opcua_xml,
)
from fb2skill_core.render import render_skill

from ..schemas.convert import ConvertResponse, Failure, SkillTtl
from ..schemas.skills import SkillListResponse


class ConversionError(Exception):
    """Raised when the request is well-formed but cannot proceed (e.g. no deploy XML)."""


def _safe_extract(zf: zipfile.ZipFile, dest: Path) -> None:
    # Zip Slip guard: reject absolute or .. members.
    for member in zf.infolist():
        name = member.filename
        if name.startswith("/") or name.startswith("\\") or ".." in Path(name).parts:
            raise ConversionError(f"unsafe zip member: {name!r}")
    zf.extractall(dest)


def _resolve_project_root(extract_root: Path) -> Path:
    """If the zip is `myproj/...`, return that single top-level dir; else extract_root."""
    children = [c for c in extract_root.iterdir() if not c.name.startswith(".")]
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return extract_root


def _do_extract_and_setup(
    zip_bytes: bytes, opcua_xml_rel_path: str | None, tmpdir: Path
) -> tuple[Path, Path]:
    with zipfile.ZipFile(_bytes_io(zip_bytes)) as zf:
        _safe_extract(zf, tmpdir)
    project_root = _resolve_project_root(tmpdir)

    if opcua_xml_rel_path:
        opcua_xml = (project_root / opcua_xml_rel_path).resolve()
        if not opcua_xml.is_file():
            raise ConversionError(f"opcua_xml_rel_path not found: {opcua_xml_rel_path}")
    else:
        opcua_xml = find_deployment_opcua_xml(project_root)
        if opcua_xml is None or not opcua_xml.is_file():
            raise ConversionError(
                "no deployment OPC UA XML found under bin/Deploy/**/; "
                "build the project in nxtControl, or pass opcua_xml_rel_path"
            )
    return project_root, opcua_xml


def _bytes_io(b: bytes):
    import io
    return io.BytesIO(b)


def convert_zip(
    zip_bytes: bytes,
    render_config: RenderConfig,
    *,
    opcua_xml_rel_path: str | None = None,
    source_zip_name: str = "project.zip",
) -> ConvertResponse:
    with tempfile.TemporaryDirectory(prefix="fb2skill-") as td:
        tmpdir = Path(td)
        project_root, opcua_xml = _do_extract_and_setup(zip_bytes, opcua_xml_rel_path, tmpdir)

        # Reseat provenance labels onto the render config (immutable dataclass).
        rc = dataclasses.replace(
            render_config,
            project_label=source_zip_name,
            source_label=opcua_xml.name,
        )

        parsed_fbts = discover_skill_fbts(project_root)
        if rc.only:
            parsed_fbts = [p for p in parsed_fbts if p.name in rc.only]

        warnings: list[str] = []
        if not parsed_fbts:
            warnings.append("no skill function blocks found")
            return ConvertResponse(skills=[], warnings=warnings, failures=[])

        node_set = load_node_set(opcua_xml, target_ns=rc.namespace_index)
        instance_names = build_instance_name_index(project_root)

        skills: list[SkillTtl] = []
        failures: list[Failure] = []
        for parsed in parsed_fbts:
            try:
                resolved = resolve_bindings(parsed, node_set, instance_names)
            except SkillResolutionError as e:
                failures.append(Failure(name=parsed.name, error=str(e)))
                continue
            ttl = render_skill(resolved, rc)
            skills.append(SkillTtl(name=resolved.name, ttl=ttl))

        return ConvertResponse(skills=skills, warnings=warnings, failures=failures)


def discover_only(
    zip_bytes: bytes,
    *,
    opcua_xml_rel_path: str | None = None,
) -> SkillListResponse:
    """Cheap discovery — no rendering, no OPC UA node-set load."""
    with tempfile.TemporaryDirectory(prefix="fb2skill-") as td:
        tmpdir = Path(td)
        with zipfile.ZipFile(_bytes_io(zip_bytes)) as zf:
            _safe_extract(zf, tmpdir)
        project_root = _resolve_project_root(tmpdir)
        parsed = discover_skill_fbts(project_root)
        names = [p.name for p in parsed]
        warnings = [] if names else ["no skill function blocks found"]
        return SkillListResponse(skills=names, warnings=warnings)
