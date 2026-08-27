# fb2skill

Convert IEC 61499 function blocks into semantic skill TTL files. Two target ontologies are supported: **MAESTRO** (default, https://w3id.org/maestro) and **CaSkMan** (CaSk / ISA-88 / DINEN61360); select with `--ontology` (CLI), the `ontology` form field (REST), or the dropdown on the web Convert page.

IEC 61499 counterpart of [PLC2Skill](https://github.com/hsu-aut/PLC2Skill). PLC2Skill targets IEC 61131-10 PLCopen XML and connects to a live OPC UA server; fb2skill targets `.fbt` files (nxtControl / EcoStruxure) and reads OPC UA node IDs from the deployment artifact offline.

## Repository layout

This is a **monorepo** with four packages under `packages/`. Three are Python (uv-workspace members); the fourth is a Node/Vite frontend.

| Package | Purpose | Entry point |
|---|---|---|
| [`fb2skill-core`](packages/fb2skill-core) | Python — domain logic (`.fbt` parser, OPC UA node resolver, Jinja renderer, ISA-88 state machine, bundled CaSkMan ontology). No CLI, no HTTP. | — |
| [`fb2skill-cli`](packages/fb2skill-cli) | Python — command-line wrapper. | `fb2skill` |
| [`fb2skill-rest`](packages/fb2skill-rest) | Python — FastAPI server exposing `/convert`, `/skills/discover`, `/ontology`, `/health`; also serves the built SPA at `/`. | `fb2skill-rest` |
| [`fb2skill-web`](packages/fb2skill-web) | TypeScript/React/Vite — SPA frontend (Convert, Discover, Ontology, State-machine viz). | `npm run dev` / `npm run build` |

See [`docs/monorepo-layout.md`](docs/monorepo-layout.md) for the architectural rationale and [`docs/divergence-from-plc2skill.md`](docs/divergence-from-plc2skill.md) for the engine-level comparison with PLC2Skill.

## Skill detection

A function block is treated as a skill iff its `<FBNetwork>` instantiates `<FB Type="BasicSKILL"/>` — the IEC 61499 analogue of PLC2Skill's `extends PLC2Skill.Skill` marker. Detection is automatic; no manifest required.

## Quick start

```
# install workspace + dev deps
uv sync

# CLI
uv run fb2skill -f <project-folder> -o <out-dir> \
                -e opc.tcp://host:4840 \
                -bI http://example.org/myproject \
                -rI my_plc \
                [--ontology maestro|caskman] [--namespace-index 2] [--only sk1,sk2] [--verify]

# REST server (listens on :8000; serves the built SPA at /)
uv run fb2skill-rest

# Web frontend — dev mode (Vite at :5173, proxies API to :8000)
cd packages/fb2skill-web && npm install && npm run dev

# Web frontend — production build (auto-served by fb2skill-rest)
cd packages/fb2skill-web && npm run build

# Docker
docker compose -f packages/fb2skill-rest/docker-compose.yml up --build
```

The deployment OPC UA file (`System.<resource>.opcua.xml` under `bin/Deploy/**/`) is auto-detected; override with `--opcua-xml` (CLI) or the `opcua_xml_rel_path` form field (REST).

## GraphDB integration

The web UI (**Tools → GraphDB**) connects to an Ontotext GraphDB server so rendered skills and the bundled
ontologies can be pushed straight into a repository, and Turtle can be downloaded back out of it.

- Connection details (URL, repository id, optional username/password) are entered in the UI and sent with
  every request; the server stores nothing. The password is kept in browser session storage only if
  "Keep password for this browser session" is ticked.
- **Upload settings**: a named-graph template (`{name}` = skill name; default `urn:fb2skill:skill:{name}`,
  empty = default graph) and a mode — *Append* adds triples, *Replace* clears the target graph first.
- Buttons: *Push all / Push <skill>* on the Convert page, *Push to GraphDB* on the Ontology page
  (graph `urn:fb2skill:ontology:<id>`), and *Download .ttl* (whole repository or one named graph) on the
  GraphDB page. *Download all (.zip)* on the Convert page now returns one zip from the server.

REST endpoints (JSON bodies; see `/docs`):

| Endpoint | Purpose |
|---|---|
| `POST /graphdb/test` | reachability, credentials, repository health, repository list |
| `POST /graphdb/graphs` | named graphs in the repository |
| `POST /graphdb/push` | upload Turtle items (`ttl` or bundled `ontology_file`) with `mode` append/replace and per-item `graph` |
| `POST /graphdb/export` | download a graph / the repository as `text/turtle` |
| `POST /export/skill`, `POST /export/skills.zip` | server-side downloads of rendered skills |

Security note: the backend opens outbound HTTP(S) connections to the user-supplied GraphDB URL, so run
`fb2skill-rest` on a trusted network only.

## Testing

```
# all packages
uv run --package fb2skill-core pytest packages/fb2skill-core/tests
uv run --package fb2skill-cli  pytest packages/fb2skill-cli/tests
uv run --package fb2skill-rest pytest packages/fb2skill-rest/tests
```

Tests requiring the FESTO example project at `D:\FESTO_DS_skills\IEC61499` are auto-skipped when that path is absent.
