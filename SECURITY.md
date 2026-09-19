# Security Policy

## What to be careful with

fb2skill reads engineering artefacts and, in one mode, listens on a network
port. Three things are worth knowing:

- **It parses untrusted XML.** `.fbt` function-block files and the
  `System.<resource>.opcua.xml` deployment artefact are XML, and an IEC 61499
  project from someone else is untrusted input. Classic XML attacks — entity
  expansion, external entity resolution — apply to anything that parses it.
- **The REST server accepts uploaded projects.** `fb2skill-rest` takes a
  project folder, walks it, and auto-detects files under `bin/Deploy/**/`. It
  has **no authentication**, so anyone who can reach port 8000 can upload a
  project and have the server parse it and write output. Run it on localhost,
  or put an authenticating proxy in front of it. Do not expose it to the
  internet.
- **Generated TTL ends up in a triplestore.** The output describes skills that
  an agent or planner may act on. Treat a skill description generated from a
  project you did not author the way you would treat code from the same source.

The converter reads OPC UA node IDs from the deployment artefact offline — it
does not connect to a live OPC UA server — so there are no OPC UA credentials
in play.

## Reporting a vulnerability

Please report privately, through
[GitHub private vulnerability reporting](https://github.com/IndustriAgents/FB2Skill/security/advisories/new),
or by email to hi@industriagents.com. Please do not open a public issue.

Include the package affected, the version or commit, what an attacker would
gain, and a reproduction. We will acknowledge within a week.

## Scope

In scope: `fb2skill-core`, `fb2skill-cli`, `fb2skill-rest` and
`fb2skill-web` in this repository, and the Docker Compose setup shipped with
the REST package.

Out of scope: vulnerabilities in FastAPI, rdflib, Jinja or the other
dependencies — report those upstream — and in nxtControl or EcoStruxure
themselves.
