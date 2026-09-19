## Summary

<!-- What does this PR do, and why? -->

## Packages touched

- [ ] `fb2skill-core`
- [ ] `fb2skill-cli`
- [ ] `fb2skill-rest`
- [ ] `fb2skill-web`
- [ ] Docs / CI only

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] New ontology target
- [ ] Documentation
- [ ] Refactor / chore

## Ontology targets exercised

- [ ] MAESTRO
- [ ] CaSkMan
- [ ] Not applicable

## Checklist

- [ ] Domain logic went into `fb2skill-core`, not into the CLI or REST adapter.
- [ ] `uv run ruff check .` and `uv run mypy packages/fb2skill-core/src` pass.
- [ ] The package test suites pass.
- [ ] Generated TTL still validates against the target ontology's shapes.
- [ ] A divergence from PLC2Skill, if any, is recorded in `docs/divergence-from-plc2skill.md`.

## Generated output

<!-- Where the TTL changed, paste a before/after sample. -->
