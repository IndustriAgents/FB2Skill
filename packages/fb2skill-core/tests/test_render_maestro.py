"""MAESTRO template-set tests on a synthetic skill (no FESTO project needed)."""
from pathlib import Path

import pytest
import rdflib
from rdflib.namespace import RDF, XSD

from fb2skill_core.config import RenderConfig
from fb2skill_core.model import OpcUaNode, Skill, SkillVariable
from fb2skill_core.render import render_skill
from fb2skill_core.state_machine import STATE_OUTGOING

CORE = rdflib.Namespace("https://w3id.org/maestro/core#")
SKILL = rdflib.Namespace("https://w3id.org/maestro/skill#")
OPCUA = rdflib.Namespace("https://w3id.org/maestro/opcua#")
COM = rdflib.Namespace("https://w3id.org/maestro/communication#")
STATE = rdflib.Namespace("https://w3id.org/maestro/state#")

BASE = "http://example.org/demo"
EX = rdflib.Namespace(BASE + "#")


def _node(guid: str, browse: str, data_type: str = "Int32") -> OpcUaNode:
    return OpcUaNode(
        node_id_guid=guid,
        namespace_idx=2,
        browse_name=browse,
        data_type=data_type,
        rt_path="",
    )


@pytest.fixture
def synthetic_skill() -> Skill:
    return Skill(
        name="skDemo",
        fbt_path=Path("skDemo.fbt"),
        interface_node=_node("11111111-1111-1111-1111-111111111111", "skDemo"),
        skill_command=_node("22222222-2222-2222-2222-222222222222", "SKILL_CMD"),
        current_state=_node("33333333-3333-3333-3333-333333333333", "CURRENT_STATE"),
        parameters=[
            SkillVariable(
                name="Speed", direction="input", iec_type="REAL", sk_type="float",
                default="0.0", required=False,
                opcua=_node("44444444-4444-4444-4444-444444444444", "Speed", "Float"),
            ),
        ],
        outputs=[
            SkillVariable(
                name="Done", direction="output", iec_type="BOOL", sk_type="bool",
                default="false", required=False,
                opcua=_node("55555555-5555-5555-5555-555555555555", "Done", "Boolean"),
            ),
        ],
    )


def _config(ontology: str) -> RenderConfig:
    return RenderConfig(
        endpoint_url="opc.tcp://plc:4840",
        base_iri=BASE,
        resource="demo_plc",
        project_label="demo.zip",
        source_label="System.demo.opcua.xml",
        ontology=ontology,
    )


@pytest.fixture
def maestro_graph(synthetic_skill) -> rdflib.Graph:
    ttl = render_skill(synthetic_skill, _config("maestro"))
    g = rdflib.Graph()
    g.parse(data=ttl, format="turtle")
    return g


def test_unknown_ontology_rejected():
    with pytest.raises(ValueError, match="unknown ontology"):
        _config("bogus")


def test_caskman_still_renders_valid_turtle(synthetic_skill):
    ttl = render_skill(synthetic_skill, _config("caskman"))
    g = rdflib.Graph()
    g.parse(data=ttl, format="turtle")
    assert len(g) > 0
    assert "hsu-aut" in ttl  # CaSkMan namespaces present


def test_resource_provides_skill(maestro_graph):
    assert (EX.demo_plc, RDF.type, CORE.Resource) in maestro_graph
    assert (EX.demo_plc, CORE.provides, EX.skDemo) in maestro_graph
    assert (EX.skDemo, RDF.type, CORE.Skill) in maestro_graph


def test_interface_shape(maestro_graph):
    iface = EX.skDemo_Interface
    assert (iface, RDF.type, OPCUA.OpcUaSkillInterface) in maestro_graph
    assert (iface, OPCUA.nodeId,
            rdflib.Literal("ns=2;g=11111111-1111-1111-1111-111111111111")) in maestro_graph
    assert (iface, OPCUA.exposes, EX.skDemo) in maestro_graph
    assert (iface, COM.exposedVia, EX.skDemo_Endpoint) in maestro_graph
    parts = set(maestro_graph.objects(iface, CORE.hasPart))
    assert {EX.skDemo_SKILL_CMD, EX.skDemo_CURRENT_STATE,
            EX.skDemo_Param_Speed, EX.skDemo_Param_Done} <= parts


def test_command_and_state_variables(maestro_graph):
    for ind, browse in (
        (EX.skDemo_SKILL_CMD, "SKILL_CMD"),
        (EX.skDemo_CURRENT_STATE, "CURRENT_STATE"),
    ):
        assert (ind, RDF.type, OPCUA.OpcUaVariable) in maestro_graph
        assert (ind, OPCUA.browseName, rdflib.Literal(browse)) in maestro_graph
        assert next(maestro_graph.objects(ind, OPCUA.nodeId), None) is not None


def test_every_parameterdef_has_paramtype(maestro_graph):
    defs = list(maestro_graph.subjects(RDF.type, SKILL.ParameterDef))
    assert len(defs) == 2
    for d in defs:
        pt = next(maestro_graph.objects(d, SKILL.paramType), None)
        assert pt is not None, f"{d} missing skill:paramType (SHACL-required)"
        assert pt.datatype == XSD.anyURI


def test_signature_inputs_and_outputs(maestro_graph):
    sig = EX.skDemo_Signature
    assert (sig, COM.hasParameterDef, EX.skDemo_Param_Speed) in maestro_graph
    assert (sig, COM.returns, EX.skDemo_Param_Done) in maestro_graph


def test_endpoint_address(maestro_graph):
    ep = EX.skDemo_Endpoint
    assert (ep, RDF.type, COM.Endpoint) in maestro_graph
    assert (ep, COM.address, rdflib.Literal("opc.tcp://plc:4840")) in maestro_graph
    assert (ep, COM.usesProtocol, COM.OpcUaProtocol) in maestro_graph


def test_state_machine_transitions(maestro_graph):
    smachine = EX.skDemo_StateMachine
    assert (smachine, RDF.type, STATE.StateMachine) in maestro_graph
    transitions = set(maestro_graph.objects(smachine, STATE.hasTransition))
    expected = sum(len(v) for v in STATE_OUTGOING.values())
    assert len(transitions) == expected
    # Every transition individual has exactly one source and one target state.
    for t in transitions:
        assert next(maestro_graph.objects(t, STATE.source), None) is not None
        assert next(maestro_graph.objects(t, STATE.target), None) is not None


def test_start_command_guard(maestro_graph):
    t = EX.skDemo_Transition_Idle_StartCommand
    assert (t, STATE.source, EX.skDemo_State_Idle) in maestro_graph
    assert (t, STATE.target, EX.skDemo_State_Starting) in maestro_graph
    assert (t, STATE.guardExpression, rdflib.Literal("SKILL_CMD=1")) in maestro_graph


def test_idle_is_initial_state(maestro_graph):
    assert (EX.skDemo_State_Idle, RDF.type, STATE.InitialState) in maestro_graph
