---
name: Bug report
about: A conversion fails, or produces the wrong TTL
title: "[Bug] "
labels: bug
assignees: ""
---

**Which package?**
- [ ] `fb2skill-core`
- [ ] `fb2skill-cli`
- [ ] `fb2skill-rest`
- [ ] `fb2skill-web`

**How did you run it?**
- [ ] CLI (`fb2skill`)
- [ ] REST (`/convert`, `/skills/discover`, …)
- [ ] Web UI

**Target ontology**
- [ ] MAESTRO (`--ontology maestro`)
- [ ] CaSkMan (`--ontology caskman`)

**Describe the bug**
What happened, and what you expected instead.

**Command or request**
```
the exact CLI invocation, or the request body / form fields
```

**Output**
```
the error, or the generated TTL with the wrong part marked
```

**The function block**
The relevant part of the `.fbt` file, if you can share it. A block that does
not convert is far easier to fix with the block in hand — redact what you need
to, but keep the `<FBNetwork>`.

**Environment**
- OS:
- Python version:
- Engineering tool the project came from (nxtControl / EcoStruxure / other):
- Commit SHA:
