# -----------------------------------------------------------------------------
# REMOVE ONE SKILL  --  the normal case.
#
# fb2skill pushes each skill into its own named graph (default template
# urn:fb2skill:skill:{name}), so removing a skill is just dropping that graph.
# Nothing else in the repository is touched.
#
# Run 01-list-skills.rq first and copy the exact ?graph value you want gone.
#
# SILENT means "do not error if the graph does not exist". Drop the SILENT
# keyword if you would rather be told that you got the name wrong.
#
# EDIT the graph IRI. As shipped it matches nothing.
# -----------------------------------------------------------------------------

DROP SILENT GRAPH <urn:fb2skill:skill:skREPLACE_ME>
