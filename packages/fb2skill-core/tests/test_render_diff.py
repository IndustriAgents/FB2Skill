import pytest

from .conftest import requires_festo
from fb2skill_core.config import RenderConfig
from fb2skill_core.opcua_nodes import load_node_set, resolve_bindings
from fb2skill_core.project import discover_skill_fbts, find_deployment_opcua_xml
from fb2skill_core.render import render_skill
from fb2skill_core.verify import diff_report, graphs_isomorphic, parse_file, parse_ttl


@pytest.fixture
def render_config_for(festo_root):
    def make():
        opcua_xml = find_deployment_opcua_xml(festo_root)
        return RenderConfig(
            endpoint_url="opc.tcp://host.docker.internal:4840",
            base_iri="http://www.ltu.se/aut/ontologies/FESTO_DS_skills",
            resource="soft_dPAC_PLC1",
            namespace_index=2,
            project_label=str(festo_root),
            source_label=opcua_xml.name,
            # The exemplar TTLs are CaSkMan; pin explicitly since the
            # RenderConfig default is maestro.
            ontology="caskman",
        )
    return make


@requires_festo
@pytest.mark.parametrize("name", ["skLoad", "skPush", "skTransfer"])
def test_render_matches_exemplar(name, festo_root, exemplars_dir, render_config_for):
    config = render_config_for()
    ns = load_node_set(find_deployment_opcua_xml(festo_root), target_ns=config.namespace_index)
    by_name = {p.name: p for p in discover_skill_fbts(festo_root)}
    skill = resolve_bindings(by_name[name], ns)
    ttl = render_skill(skill, config)
    expected = parse_file(exemplars_dir / f"{name}.ttl")
    actual = parse_ttl(ttl)
    assert graphs_isomorphic(actual, expected), diff_report(actual, expected)


@requires_festo
@pytest.mark.parametrize("name", ["skLoad", "skPush", "skTransfer"])
def test_render_is_valid_turtle(name, festo_root, render_config_for):
    config = render_config_for()
    ns = load_node_set(find_deployment_opcua_xml(festo_root), target_ns=config.namespace_index)
    by_name = {p.name: p for p in discover_skill_fbts(festo_root)}
    skill = resolve_bindings(by_name[name], ns)
    ttl = render_skill(skill, config)
    parse_ttl(ttl)  # raises on bad syntax
