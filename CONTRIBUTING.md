# Contributing to fb2skill

Thanks for taking an interest. fb2skill turns IEC 61499 function blocks into
semantic skill descriptions, against either the
[MAESTRO](https://github.com/IndustriAgents/MAESTRO) or the CaSkMan ontology.
It is a monorepo of four packages, and which one you are in changes how you
work.

| Package | What it is | Managed by |
|---|---|---|
| [`fb2skill-core`](packages/fb2skill-core) | The domain logic — `.fbt` parser, OPC UA node resolver, Jinja renderer, ISA-88 state machine | uv |
| [`fb2skill-cli`](packages/fb2skill-cli) | Command-line wrapper | uv |
| [`fb2skill-rest`](packages/fb2skill-rest) | FastAPI server; also serves the built SPA | uv |
| [`fb2skill-web`](packages/fb2skill-web) | React/Vite frontend | npm |

The three Python packages are members of a single
[uv](https://docs.astral.sh/uv/) workspace; `fb2skill-web` is deliberately
excluded from it and managed with npm.
[`docs/monorepo-layout.md`](docs/monorepo-layout.md) has the rationale.

## Getting set up

```bash
uv sync                                  # workspace + dev deps (pytest, ruff, mypy)

uv run fb2skill --help                   # CLI
uv run fb2skill-rest                     # REST on :8000, serves the SPA at /

cd packages/fb2skill-web && npm install && npm run dev   # Vite on :5173, proxies to :8000
```

## Running the tests

```bash
uv run --package fb2skill-core pytest packages/fb2skill-core/tests
uv run --package fb2skill-cli  pytest packages/fb2skill-cli/tests
uv run --package fb2skill-rest pytest packages/fb2skill-rest/tests
```

Tests that need the FESTO example project are skipped automatically when that
path is absent, so a clean checkout passes without it. If your change depends
on a real project, add a fixture rather than a second skip — a test that only
runs on one machine is a test nobody runs.

Lint and type-check before opening a pull request:

```bash
uv run ruff check .
uv run mypy packages/fb2skill-core/src
```

## Where a change belongs

Most of the pull requests that need rework put logic in the wrong layer, so:

- **`fb2skill-core` owns the domain.** Parsing, resolution, rendering and the
  state machine live here. It has no CLI and no HTTP, on purpose — both of the
  other two are thin wrappers over it, and anything that goes in one of them
  has to be reimplemented in the other.
- **`fb2skill-cli` and `fb2skill-rest` are adapters.** Argument parsing,
  request handling, file upload, error formatting. If you find yourself writing
  a rule about function blocks in either, it belongs in core.
- **Ontology output is templated.** A new target ontology is a renderer and its
  templates, selectable through `--ontology`, not a fork of the converter.

## House rules

- **Skill detection is structural.** A function block is a skill iff its
  `<FBNetwork>` instantiates `<FB Type="BasicSKILL"/>`. There is no manifest and
  no naming convention, and adding one would change what the tool is.
- **Generated TTL must validate.** If you change a template, check the output
  against the shapes in the target ontology — MAESTRO ships SHACL shapes for
  exactly this.
- Keep `--ontology maestro` and `--ontology caskman` at parity where the
  ontologies allow it, and say so in the pull request where they cannot be.
- Document a divergence from [PLC2Skill](https://github.com/hsu-aut/PLC2Skill)
  in [`docs/divergence-from-plc2skill.md`](docs/divergence-from-plc2skill.md).
  The comparison is part of what makes this repository useful.

## Pull requests

Say which packages you touched, which ontology targets you exercised, and paste
a sample of the generated TTL where the output changed.

## Code of Conduct

By taking part you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
