import io
import zipfile

import pytest

from fb2skill_core.verify import diff_report, graphs_isomorphic, parse_file, parse_ttl

from .conftest import requires_festo  # noqa: F401

# demo_zip fixture lives in conftest.py

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
