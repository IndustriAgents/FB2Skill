# -----------------------------------------------------------------------------
# REMOVE ONE SKILL  --  when it does NOT have its own named graph.
#
# Use this when the named-graph template was left empty (everything went into
# the default graph) or when several skills share one graph, so 10-... would
# take the other skills with it. Deletes the skill's own triples wherever they
# live and leaves everything else alone.
#
# >>> RUN 04-preview-skill-triples.rq WITH THE SAME NAME FIRST. <<<
# It uses an identical WHERE clause and shows you the exact rows this deletes.
#
# Deliberately NOT deleted, because they are shared with other skills:
#   - the Resource individual's own type triples (CSS:Resource / core:Resource)
#   - OpcUa:AnonymousIdentityToken rdfs:subClassOf OpcUa:UserIdentityToken
# The links FROM the resource TO this skill (CSS:providesSkill, core:provides)
# ARE deleted -- that is what the object-position half of the FILTER does.
#
# EDIT the skill name on the BIND line. As shipped it matches nothing.
# -----------------------------------------------------------------------------

PREFIX core: <https://w3id.org/maestro/core#>
PREFIX CSS:  <http://www.w3id.org/hsu-aut/css#>

DELETE { GRAPH ?g { ?s ?p ?o } }
WHERE {
  {
    SELECT ?iri
    WHERE {
      #        vvvvvvvvvvvv  <-- the skill you want gone
      BIND("skREPLACE_ME" AS ?skillName)
      GRAPH ?skillGraph { ?skill a ?skillClass }
      FILTER(?skillClass IN (core:Skill, CSS:Skill))
      FILTER(STRENDS(STR(?skill), CONCAT("#", ?skillName)))
      BIND(STR(?skill) AS ?iri)
    }
  }
  GRAPH ?g { ?s ?p ?o }
  FILTER(
       STR(?s) = ?iri
    || STRSTARTS(STR(?s), CONCAT(?iri, "_"))
    || (isIRI(?o) && (STR(?o) = ?iri || STRSTARTS(STR(?o), CONCAT(?iri, "_"))))
  )
}
