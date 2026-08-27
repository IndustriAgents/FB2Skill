import io
import zipfile

TTL = "@prefix ex: <http://example.org/> .\nex:a ex:b ex:c .\n"


def test_export_single_skill(client):
    r = client.post("/export/skill", json={"name": "sk Load/1", "ttl": TTL})
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/turtle")
    assert r.headers["content-disposition"] == 'attachment; filename="sk_Load_1.ttl"'
    assert r.text == TTL


def test_export_zip_entries_and_dedup(client):
    r = client.post(
        "/export/skills.zip",
        json={
            "skills": [
                {"name": "skLoad", "ttl": TTL},
                {"name": "skLoad", "ttl": TTL},  # duplicate name -> _2 suffix
            ],
            "include_ontology": [{"ontology_id": "caskman", "file_path": "CaSkMan_v4.3.0.ttl"}],
        },
    )
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/zip"
    assert r.headers["content-disposition"] == 'attachment; filename="skills.zip"'
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        names = zf.namelist()
        assert names == [
            "skills/skLoad.ttl",
            "skills/skLoad_2.ttl",
            "ontology/CaSkMan_v4.3.0.ttl",
        ]
        assert zf.read("skills/skLoad.ttl").decode() == TTL
        assert zf.read("ontology/CaSkMan_v4.3.0.ttl")[:2000].find(b"@prefix") >= 0


def test_export_zip_unknown_ontology_file_is_404(client):
    r = client.post(
        "/export/skills.zip",
        json={
            "skills": [{"name": "a", "ttl": TTL}],
            "include_ontology": [{"ontology_id": "caskman", "file_path": "nope.ttl"}],
        },
    )
    assert r.status_code == 404


def test_export_zip_requires_skills(client):
    r = client.post("/export/skills.zip", json={"skills": []})
    assert r.status_code == 422


def test_convert_then_zip_end_to_end(client, demo_zip):
    conv = client.post(
        "/convert",
        files={"project_zip": ("demo.zip", demo_zip, "application/zip")},
        data={"endpoint_url": "opc.tcp://x:4840", "base_iri": "http://example.org/demo", "resource": "demo_plc"},
    )
    assert conv.status_code == 200, conv.text
    r = client.post("/export/skills.zip", json={"skills": conv.json()["skills"]})
    assert r.status_code == 200, r.text
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        assert zf.namelist() == ["skills/skDemo.ttl"]
        assert b"w3id.org/maestro" in zf.read("skills/skDemo.ttl")
