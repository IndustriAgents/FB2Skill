# SPARQL queries for fb2skill skills in GraphDB

Read-only inventory queries (`.rq`) and removal updates (`.ru`) for the skills
that the fb2skill web UI pushes into an Ontotext GraphDB repository.

| File | Kind | What it does |
|---|---|---|
| [`01-list-skills.rq`](01-list-skills.rq) | query | **Which skills are uploaded** — one row per skill with its named graph, resource, OPC UA node id and endpoint URL |
| [`02-skill-detail.rq`](02-skill-detail.rq) | query | One skill's interface, state machine, parameters and outputs |
| [`03-graph-inventory.rq`](03-graph-inventory.rq) | query | Every named graph with triple count and how many skills it holds |
| [`04-preview-skill-triples.rq`](04-preview-skill-triples.rq) | query | Dry run for `11-…` — the exact triples one skill owns |
| [`05-preview-all-skill-graphs.rq`](05-preview-all-skill-graphs.rq) | query | Dry run for `12-…` — every graph the bulk delete would empty |
| [`10-remove-skill-graph.ru`](10-remove-skill-graph.ru) | update | **Remove one skill** by dropping its named graph (the normal case) |
| [`11-remove-skill-triples.ru`](11-remove-skill-triples.ru) | update | Remove one skill by triples, when it has no graph of its own |
| [`12-remove-all-skills.ru`](12-remove-all-skills.ru) | update | Remove every fb2skill skill graph — destructive |

Every file that needs a skill name ships with the placeholder `skREPLACE_ME`,
so it parses and runs but matches nothing until you edit it.

## Running them

**GraphDB Workbench** — <http://localhost:7200> → *SPARQL*. Paste a `.rq` and
press Run. For a `.ru`, paste it into the same editor; the Workbench detects an
update and switches the button to *Execute update*.

**curl** — queries go to the repository endpoint, updates to `/statements`:

```bash
curl -X POST http://localhost:7200/repositories/<repo> -H "Accept: text/csv" -H "Content-Type: application/sparql-query" --data-binary @sparql/01-list-skills.rq
```

```bash
curl -X POST http://localhost:7200/repositories/<repo>/statements -H "Content-Type: application/sparql-update" --data-binary @sparql/10-remove-skill-graph.ru
```

A successful update returns `204 No Content` and prints nothing — that is normal.

**The fb2skill web UI** does not run SPARQL, but *Tools → GraphDB* lists the
named graphs and downloads any of them as Turtle, which is the quickest way to
take a backup before deleting.

## How skills are laid out

fb2skill pushes **one skill per named graph**, named from the template on the
GraphDB page — by default `urn:fb2skill:skill:{name}`. Pushed ontologies go to
`urn:fb2skill:ontology:<id>`. That convention is what makes removal easy, but
none of the `.rq` files depend on it: they find skills by RDF type, so they also
work if you changed the template or pushed into the default graph.

A skill is typed according to the target ontology it was rendered for:

| Ontology | Skill class | Resource link |
|---|---|---|
| MAESTRO | `<https://w3id.org/maestro/core#Skill>` | `core:provides` |
| CaSkMan | `<http://www.w3id.org/hsu-aut/css#Skill>` (also `CaSkMan:PlcSkill`) | `CSS:providesSkill` |

The queries cover both, so a repository holding a mix reports them together
with a `?vocabulary` column telling them apart.

Everything else a skill owns is named after it —  `<skill>_Interface`,
`<skill>_StateMachine`, `<skill>_Param_*`, `<skill>_SkillCommand`, and so on.
That naming is what `04-…` and `11-…` use to scope a delete.

## Removing skills: which file

**Has its own named graph?** Use `10-remove-skill-graph.ru`. Dropping the graph
removes the skill completely and cannot affect anything else. This is the case
for anything pushed with the default template.

**Shares a graph, or went into the default graph?** Use
`11-remove-skill-triples.ru`, after previewing with `04-…`. It deletes the
skill's own individuals plus the links pointing at them.

Two kinds of triple survive `11-…` on purpose, because other skills still need
them:

- the Resource individual's own type triples (`:soft_dPAC_PLC1 a core:Resource`)
- `OpcUa:AnonymousIdentityToken rdfs:subClassOf OpcUa:UserIdentityToken`, which
  the CaSkMan template asserts so CaSkade-MES can resolve an endpoint without
  the full OPC UA ontology loaded

The *links* from the resource to the skill (`core:provides` /
`CSS:providesSkill`) are removed. If you delete the last skill on a resource,
that resource individual is left behind as a stub; drop it by hand if you want
it gone.

## Before you delete

There is no undo. Back the repository up first, in **TriG** — unlike Turtle it
records which named graph each statement belongs to, so a restore rebuilds the
per-skill split instead of collapsing everything into the default graph:

```bash
curl -H "Accept: application/x-trig" "http://localhost:7200/repositories/<repo>/statements" > backup.trig
```

Restore it with:

```bash
curl -X POST "http://localhost:7200/repositories/<repo>/statements" -H "Content-Type: application/x-trig" --data-binary @backup.trig
```

The web UI's *Download .ttl* and a plain `Accept: text/turtle` export are fine
for reading a single graph, but Turtle has no syntax for named graphs — a
whole-repository Turtle export flattens every skill into one pile. Use it per
graph (select a graph on the GraphDB page, or append
`?context=%3Curn:fb2skill:skill:skLoad%3E` to the export URL) or use TriG.

Then run the matching preview (`04-…` or `05-…`) and check the rows before
running the delete.
