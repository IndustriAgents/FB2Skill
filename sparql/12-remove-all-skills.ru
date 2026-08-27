# -----------------------------------------------------------------------------
# REMOVE EVERY fb2skill SKILL GRAPH.  DESTRUCTIVE -- READ THIS FIRST.
#
# Clears every named graph whose IRI starts with the fb2skill skill prefix.
# There is no undo. Take a backup first -- the GraphDB page in the web UI has
# "Download .ttl" (whole repository), or:
#
#   curl -H "Accept: text/turtle" \
#     "http://localhost:7200/repositories/<repo>/statements" > backup.ttl
#
# >>> RUN 03-graph-inventory.rq FIRST <<< and confirm that the graphs listed
# under urn:fb2skill:skill: are all ones you are willing to lose.
#
# Pushed ontologies (urn:fb2skill:ontology:*) and anything outside the
# urn:fb2skill:skill: prefix are NOT touched by this.
#
# Narrow the prefix to delete a subset, e.g.
#   "urn:fb2skill:skill:skSwivelArm"  -> only the skSwivelArm_* skills.
# -----------------------------------------------------------------------------

DELETE { GRAPH ?g { ?s ?p ?o } }
WHERE {
  GRAPH ?g { ?s ?p ?o }
  #                            vvvvvvvvvvvvvvvvvvvvv  <-- narrow this to scope it
  FILTER(STRSTARTS(STR(?g), "urn:fb2skill:skill:"))
}
