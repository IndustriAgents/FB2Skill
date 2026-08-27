import pytest

from fb2skill_rest.services import graphdb as graphdb_service

from .graphdb_mock import CANNED_TTL, FakeGraphDB

CONN = {"base_url": "http://graphdb.test:7200", "repository": "fb2skill"}
TTL = "@prefix ex: <http://example.org/> .\nex:a ex:b ex:c .\n"


@pytest.fixture
def fake(monkeypatch) -> FakeGraphDB:
    fake = FakeGraphDB()
    monkeypatch.setattr(graphdb_service, "_transport_factory", fake.transport)
    return fake


# --- /graphdb/test ----------------------------------------------------------


def test_connection_ok(client, fake):
    r = client.post("/graphdb/test", json={"connection": CONN})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["repository_found"] and body["repository_healthy"]
    assert body["protocol"] == "12.0"
    assert [x["id"] for x in body["repositories"]] == ["fb2skill"]


def test_connection_repo_missing_is_reported_not_error(client, fake):
    r = client.post("/graphdb/test", json={"connection": {**CONN, "repository": "nope"}})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is False and body["repository_found"] is False
    assert "nope" in body["message"]


def test_connection_unreachable_is_502(client, fake):
    fake.unreachable = True
    r = client.post("/graphdb/test", json={"connection": CONN})
    assert r.status_code == 502
    assert "Cannot reach GraphDB" in r.json()["detail"]


def test_connection_bad_credentials_is_401(client, fake):
    fake.auth = ("admin", "root")
    r = client.post(
        "/graphdb/test",
        json={"connection": {**CONN, "username": "admin", "password": "wrong"}},
    )
    assert r.status_code == 401


def test_connection_good_credentials(client, fake):
    fake.auth = ("admin", "root")
    r = client.post(
        "/graphdb/test",
        json={"connection": {**CONN, "username": "admin", "password": "root"}},
    )
    assert r.status_code == 200 and r.json()["ok"] is True


def test_connection_rejects_non_http_url(client, fake):
    r = client.post("/graphdb/test", json={"connection": {**CONN, "base_url": "ftp://x"}})
    assert r.status_code == 422


# --- /graphdb/graphs --------------------------------------------------------


def test_list_graphs(client, fake):
    r = client.post("/graphdb/graphs", json={"connection": CONN})
    assert r.status_code == 200, r.text
    assert r.json() == {"graphs": ["urn:fb2skill:skill:skOld"]}


# --- /graphdb/push ----------------------------------------------------------


def _push(client, items, mode="append", conn=CONN):
    return client.post("/graphdb/push", json={"connection": conn, "mode": mode, "items": items})


def test_push_append_default_graph(client, fake):
    r = _push(client, [{"name": "skDemo", "ttl": TTL}])
    assert r.status_code == 200, r.text
    (res,) = r.json()["results"]
    assert res["ok"] is True and res["triples"] == 3 and res["graph"] is None
    (w,) = fake.writes
    assert w.method == "POST" and "context" not in w.params
    assert w.headers["content-type"] == "text/turtle"
    assert w.body == TTL.encode()


def test_push_append_named_graph(client, fake):
    r = _push(client, [{"name": "skDemo", "ttl": TTL, "graph": "urn:fb2skill:skill:skDemo"}])
    assert r.status_code == 200, r.text
    (w,) = fake.writes
    assert w.method == "POST"
    assert w.params["context"] == "<urn:fb2skill:skill:skDemo>"


def test_push_replace_named_graph_uses_put(client, fake):
    r = _push(
        client,
        [{"name": "skDemo", "ttl": TTL, "graph": "urn:fb2skill:skill:skDemo"}],
        mode="replace",
    )
    assert r.status_code == 200, r.text
    (w,) = fake.writes
    assert w.method == "PUT"
    assert w.params["context"] == "<urn:fb2skill:skill:skDemo>"


def test_push_replace_default_graph_uses_null_context(client, fake):
    r = _push(client, [{"name": "skDemo", "ttl": TTL}], mode="replace")
    assert r.status_code == 200, r.text
    (w,) = fake.writes
    assert w.method == "PUT" and w.params["context"] == "null"


def test_push_bad_turtle_is_per_item_error(client, fake):
    r = _push(
        client,
        [
            {"name": "good", "ttl": TTL, "graph": "urn:g1"},
            {"name": "bad", "ttl": "BAD", "graph": "urn:g2"},
        ],
    )
    assert r.status_code == 200, r.text
    good, bad = r.json()["results"]
    assert good["ok"] is True
    assert bad["ok"] is False and "rejected Turtle" in bad["error"]


def test_push_ontology_file_reads_bundled_ttl(client, fake):
    r = _push(
        client,
        [
            {
                "name": "CaSkMan",
                "graph": "urn:fb2skill:ontology:caskman",
                "ontology_file": {"ontology_id": "caskman", "file_path": "CaSkMan_v4.3.0.ttl"},
            }
        ],
    )
    assert r.status_code == 200, r.text
    assert r.json()["results"][0]["ok"] is True
    (w,) = fake.writes
    assert b"@prefix" in w.body[:2000]
    assert w.params["context"] == "<urn:fb2skill:ontology:caskman>"


def test_push_unknown_ontology_file_is_per_item_error(client, fake):
    r = _push(
        client,
        [{"name": "x", "ontology_file": {"ontology_id": "caskman", "file_path": "../etc/passwd"}}],
    )
    assert r.status_code == 200, r.text
    (res,) = r.json()["results"]
    assert res["ok"] is False and "unknown ontology file" in res["error"]
    assert fake.writes == []


def test_push_item_needs_exactly_one_source(client, fake):
    r = _push(client, [{"name": "x"}])
    assert r.status_code == 422
    r = _push(
        client,
        [{"name": "x", "ttl": TTL, "ontology_file": {"ontology_id": "caskman", "file_path": "a"}}],
    )
    assert r.status_code == 422


def test_push_unknown_repository_is_404(client, fake):
    r = _push(client, [{"name": "skDemo", "ttl": TTL}], conn={**CONN, "repository": "nope"})
    assert r.status_code == 404
    assert fake.writes == []


# --- /graphdb/export --------------------------------------------------------


def test_export_whole_repository(client, fake):
    r = client.post("/graphdb/export", json={"connection": CONN})
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/turtle")
    assert r.headers["content-disposition"] == 'attachment; filename="fb2skill.ttl"'
    assert r.text == CANNED_TTL
    (rd,) = fake.reads
    assert "context" not in rd.params and rd.params["infer"] == "false"
    assert rd.headers["accept"] == "text/turtle"


def test_export_named_graph(client, fake):
    r = client.post(
        "/graphdb/export",
        json={"connection": CONN, "graph": "urn:fb2skill:skill:skDemo", "infer": True},
    )
    assert r.status_code == 200, r.text
    assert "fb2skill-urn_fb2skill_skill_skDemo.ttl" in r.headers["content-disposition"]
    (rd,) = fake.reads
    assert rd.params["context"] == "<urn:fb2skill:skill:skDemo>"
    assert rd.params["infer"] == "true"


def test_export_unreachable_is_502(client, fake):
    fake.unreachable = True
    r = client.post("/graphdb/export", json={"connection": CONN})
    assert r.status_code == 502
