import io
import zipfile

import pytest

from fb2skill_core.verify import diff_report, graphs_isomorphic, parse_file, parse_ttl

from .conftest import requires_festo

_DEMO_FBT = """<?xml version="1.0" encoding="UTF-8"?>
<FBType Name="skDemo">
  <InterfaceList>
    <InputVars><VarDeclaration Name="Speed" Type="REAL"/></InputVars>
    <OutputVars><VarDeclaration Name="Done" Type="BOOL"/></OutputVars>
  </InterfaceList>
  <FBNetwork><FB Name="Skill_Commands" Type="BasicSKILL"/></FBNetwork>
</FBType>
"""

_DEMO_OPCUA_XML = """<?xml version="1.0" encoding="utf-8"?>
<UANodeSet xmlns="http://opcfoundation.org/UA/2011/03/UANodeSet.xsd">
  <UAObject NodeId="ns=1;g=11111111-1111-1111-1111-111111111111" BrowseName="1:skDemo"/>
  <UAVariable NodeId="ns=1;g=22222222-2222-2222-2222-222222222222" BrowseName="1:SKILL_CMD" DataType="Int32">
    <Extensions><Extension><RTAddress xmlns="">V1;Path=PLC1.RES0.skDemo.Skill_Commands.IThis.SKILL_CMD;Trigger=INPUT</RTAddress></Extension></Extensions>
  </UAVariable>
  <UAVariable NodeId="ns=1;g=33333333-3333-3333-3333-333333333333" BrowseName="1:CURRENT_STATE" DataType="Int32">
    <Extensions><Extension><RTAddress xmlns="">V1;Path=PLC1.RES0.skDemo.Skill_Commands.IThis.CURRENT_STATE</RTAddress></Extension></Extensions>
  </UAVariable>
  <UAVariable NodeId="ns=1;g=44444444-4444-4444-4444-444444444444" BrowseName="1:Speed" DataType="Float">
    <Extensions><Extension><RTAddress xmlns="">V1;Path=PLC1.RES0.skDemo.Skill_Commands.IThis.Speed;Trigger=INPUT</RTAddress></Extension></Extensions>
  </UAVariable>
  <UAVariable NodeId="ns=1;g=55555555-5555-5555-5555-555555555555" BrowseName="1:Done" DataType="Boolean">
    <Extensions><Extension><RTAddress xmlns="">V1;Path=PLC1.RES0.skDemo.Skill_Commands.IThis.Done</RTAddress></Extension></Extensions>
  </UAVariable>
</UANodeSet>
"""


@pytest.fixture
def demo_zip() -> bytes:
    """Minimal synthetic project: one BasicSKILL fbt + deployment OPC UA XML."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("DemoProj/skDemo.fbt", _DEMO_FBT)
        zf.writestr("DemoProj/bin/Deploy/PLC1/System.demo.opcua.xml", _DEMO_OPCUA_XML)
    return buf.getvalue()


_DEMO_FIELDS = {
    "endpoint_url": "opc.tcp://x:4840",
    "base_iri": "http://example.org/demo",
    "resource": "demo_plc",
}


def test_convert_maestro_ontology(client, demo_zip):
    r = client.post(
        "/convert",
        files={"project_zip": ("demo.zip", demo_zip, "application/zip")},
        data={**_DEMO_FIELDS, "ontology": "maestro"},
    )
    assert r.status_code == 200, r.text
    skills = r.json()["skills"]
    assert [s["name"] for s in skills] == ["skDemo"]
    ttl = skills[0]["ttl"]
    assert "w3id.org/maestro" in ttl
    assert len(parse_ttl(ttl)) > 0


def test_convert_defaults_to_maestro(client, demo_zip):
    r = client.post(
        "/convert",
        files={"project_zip": ("demo.zip", demo_zip, "application/zip")},
        data=_DEMO_FIELDS,
    )
    assert r.status_code == 200, r.text
    ttl = r.json()["skills"][0]["ttl"]
    assert "w3id.org/maestro" in ttl
    assert "hsu-aut" not in ttl


def test_convert_caskman_selectable(client, demo_zip):
    r = client.post(
        "/convert",
        files={"project_zip": ("demo.zip", demo_zip, "application/zip")},
        data={**_DEMO_FIELDS, "ontology": "caskman"},
    )
    assert r.status_code == 200, r.text
    ttl = r.json()["skills"][0]["ttl"]
    assert "hsu-aut" in ttl
    assert "w3id.org/maestro" not in ttl


def test_convert_rejects_unknown_ontology(client, demo_zip):
    r = client.post(
        "/convert",
        files={"project_zip": ("demo.zip", demo_zip, "application/zip")},
        data={**_DEMO_FIELDS, "ontology": "bogus"},
    )
    assert r.status_code == 422
    assert "unknown ontology" in r.json()["detail"]


@requires_festo
def test_convert_matches_exemplars(client, festo_zip, exemplars_dir):
    r = client.post(
        "/convert",
        files={"project_zip": ("festo.zip", festo_zip, "application/zip")},
        data={
            "endpoint_url": "opc.tcp://host.docker.internal:4840",
            "base_iri": "http://www.ltu.se/aut/ontologies/FESTO_DS_skills",
            "resource": "soft_dPAC_PLC1",
            "namespace_index": "2",
        },
    )
    assert r.status_code == 200, r.text
    payload = r.json()
    by_name = {s["name"]: s["ttl"] for s in payload["skills"]}

    for name in ("skLoad", "skPush", "skTransfer"):
        assert name in by_name, f"missing {name} in response"
        actual = parse_ttl(by_name[name])
        expected = parse_file(exemplars_dir / f"{name}.ttl")
        assert graphs_isomorphic(actual, expected), diff_report(actual, expected)

    # Nested-only skills (skPick etc.) should appear in `failures`, not `skills`.
    failure_names = {f["name"] for f in payload["failures"]}
    assert {"skPick", "skPlace", "skGoToLeft", "skGoToRight"} <= failure_names


@requires_festo
def test_convert_with_only_filter(client, festo_zip):
    r = client.post(
        "/convert",
        files={"project_zip": ("festo.zip", festo_zip, "application/zip")},
        data={
            "endpoint_url": "opc.tcp://x",
            "base_iri": "http://x",
            "resource": "soft_dPAC_PLC1",
            "only": "skLoad",
        },
    )
    assert r.status_code == 200
    assert {s["name"] for s in r.json()["skills"]} == {"skLoad"}


def test_convert_rejects_empty_zip(client):
    import io, zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("placeholder.txt", "no fbts here")
    r = client.post(
        "/convert",
        files={"project_zip": ("empty.zip", buf.getvalue(), "application/zip")},
        data={
            "endpoint_url": "opc.tcp://x",
            "base_iri": "http://x",
            "resource": "x",
        },
    )
    # Either 200 with empty skills + warning, or 422 if deploy XML missing — both acceptable.
    assert r.status_code in (200, 422)
    if r.status_code == 200:
        body = r.json()
        assert body["skills"] == []
        assert body["warnings"]
