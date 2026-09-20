# fb2skill

[![License: MIT](https://img.shields.io/github/license/IndustriAgents/FB2Skill)](LICENSE)
[![Ontologies](https://img.shields.io/badge/ontologies-MAESTRO%20%7C%20CaSkMan-4c6ef5)](#)
[![IEC 61499](https://img.shields.io/badge/IEC-61499-0b7285)](https://www.iec.ch/)

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

## Testing

```
# all packages
uv run --package fb2skill-core pytest packages/fb2skill-core/tests
uv run --package fb2skill-cli  pytest packages/fb2skill-cli/tests
uv run --package fb2skill-rest pytest packages/fb2skill-rest/tests
```

Tests requiring the FESTO example project at `D:\FESTO_DS_skills\IEC61499` are auto-skipped when that path is absent.

## Contributing

Contributions are welcome. [CONTRIBUTING.md](CONTRIBUTING.md) covers the
workspace layout, how to run the tests, and which of the four packages a change
belongs in — the usual rework is domain logic that landed in an adapter rather
than in `fb2skill-core`. Please also read the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Security

`fb2skill-rest` parses uploaded engineering projects and has no authentication
of its own. [SECURITY.md](SECURITY.md) explains what that means and how to
report a vulnerability privately.

## License

Released under the [MIT License](LICENSE).
