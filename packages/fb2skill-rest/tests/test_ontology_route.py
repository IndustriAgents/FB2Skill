import rdflib


def test_ontology_returns_turtle(client):
    r = client.get("/ontology")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/turtle")
    # Body must parse as Turtle.
    g = rdflib.Graph()
    g.parse(data=r.content, format="turtle")
    assert len(g) > 0


def test_ontologies_manifest(client):
    r = client.get("/ontologies")
    assert r.status_code == 200
    ids = {o["id"] for o in r.json()["ontologies"]}
    assert ids == {"caskman", "maestro"}
    maestro = next(o for o in r.json()["ontologies"] if o["id"] == "maestro")
    assert maestro["version"] == "0.4.0"
    group_ids = [g["id"] for g in maestro["groups"]]
    assert "references" in group_ids
    refs = next(g for g in maestro["groups"] if g["id"] == "references")
    assert "references/caskman.ttl" in refs["files"]


def test_maestro_file_returns_turtle(client):
    r = client.get("/ontologies/maestro/files/runtime/state.ttl")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/turtle")
    g = rdflib.Graph()
    g.parse(data=r.content, format="turtle")
    assert len(g) > 0


def test_caskman_file_via_new_route(client):
    r = client.get("/ontologies/caskman/files/CaSkMan_v4.3.0.ttl")
    assert r.status_code == 200


def test_unknown_ontology_404(client):
    assert client.get("/ontologies/bogus/files/x.ttl").status_code == 404


def test_unlisted_path_404(client):
    # Real file in the package, but not in the manifest allowlist.
    assert client.get("/ontologies/maestro/files/manifest.json").status_code == 404


def test_traversal_404(client):
    assert client.get(
        "/ontologies/maestro/files/../CaSkMan_v4.3.0.ttl"
    ).status_code == 404
