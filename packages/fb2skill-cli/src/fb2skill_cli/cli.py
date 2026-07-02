"""``fb2skill`` command-line entry point."""
import argparse
import sys
from pathlib import Path

from fb2skill_core.config import ONTOLOGIES, RenderConfig
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

from .config import CliConfig


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fb2skill",
        description="Convert IEC 61499 function blocks into semantic skill TTL files "
                    "(CaSk/CaSkMan or MAESTRO vocabulary).",
    )
    p.add_argument("-f", "--project", required=True, type=Path,
                   help="IEC 61499 project root folder")
    p.add_argument("-o", "--out-dir", default=Path("./out"), type=Path,
                   help="output directory (default: ./out)")
    p.add_argument("--opcua-xml", type=Path, default=None,
                   help="path to deployment System.<resource>.opcua.xml "
                        "(default: auto-detect under <project>/**/bin/Deploy/**/)")
    p.add_argument("-e", "--endpoint", required=True,
                   help="OPC UA endpoint URL written into the generated TTL")
    p.add_argument("-bI", "--base-iri", required=True,
                   help='base IRI for the default ":" prefix')
    p.add_argument("-rI", "--resource", required=True,
                   help="local name of the CSS:Resource individual")
    p.add_argument("-n", "--namespace-index", type=int, default=2,
                   help="OPC UA namespace index to emit in node IDs (default: 2)")
    p.add_argument("--only", default="",
                   help="comma-separated FB-name allowlist (default: all detected skills)")
    p.add_argument("--ontology", choices=ONTOLOGIES, default="maestro",
                   help="target ontology vocabulary (default: maestro)")
    p.add_argument("--verify", action="store_true",
                   help="parse each generated TTL with rdflib after writing")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    project_root: Path = args.project
    if not project_root.is_dir():
        print(f"error: project path is not a directory: {project_root}", file=sys.stderr)
        return 2

    opcua_xml = args.opcua_xml or find_deployment_opcua_xml(project_root)
    if opcua_xml is None or not opcua_xml.is_file():
        print(
            f"error: could not locate deployment OPC UA XML under {project_root}; "
            "did you build the project in nxtControl?",
            file=sys.stderr,
        )
        return 2

    only = tuple(s for s in args.only.split(",") if s)

    render_config = RenderConfig(
        endpoint_url=args.endpoint,
        base_iri=args.base_iri,
        resource=args.resource,
        namespace_index=args.namespace_index,
        project_label=str(project_root),
        source_label=opcua_xml.name,
        only=only,
        ontology=args.ontology,
    )
    config = CliConfig(
        project_root=project_root,
        out_dir=args.out_dir,
        opcua_xml=opcua_xml,
        render=render_config,
        verify=args.verify,
    )

    parsed_fbts = discover_skill_fbts(project_root)
    if only:
        parsed_fbts = [p for p in parsed_fbts if p.name in only]

    if not parsed_fbts:
        print("warning: no skill function blocks found", file=sys.stderr)
        return 0

    node_set = load_node_set(opcua_xml, target_ns=render_config.namespace_index)
    instance_names = build_instance_name_index(project_root)
    config.out_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    verify_failures = 0
    for parsed in parsed_fbts:
        try:
            skill = resolve_bindings(parsed, node_set, instance_names)
        except SkillResolutionError as e:
            print(f"skip {parsed.name}: {e}", file=sys.stderr)
            failures += 1
            continue
        ttl = render_skill(skill, render_config)
        out_path = config.out_dir / f"{skill.name}.ttl"
        out_path.write_text(ttl, encoding="utf-8")
        print(f"wrote {out_path}")

        if config.verify:
            try:
                import rdflib
                rdflib.Graph().parse(data=ttl, format="turtle")
            except Exception as e:
                print(f"  ! verification failed: {e}", file=sys.stderr)
                verify_failures += 1

    if verify_failures:
        return 3
    return 0
