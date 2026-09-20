---
name: Feature request
about: Suggest an improvement or a new ontology target
title: "[Feature] "
labels: enhancement
assignees: ""
---

**What problem does this solve?**
The use case, from the point of view of someone converting a project.

**Which package would it touch?**
- [ ] `fb2skill-core`
- [ ] `fb2skill-cli`
- [ ] `fb2skill-rest`
- [ ] `fb2skill-web`
- [ ] Not sure

**Proposed solution**
What you would like to happen. If it changes the generated TTL, show the
triples you expect.

**Which ontology targets?**
- [ ] MAESTRO
- [ ] CaSkMan
- [ ] A new target — which one, and where is it specified:

**Does it change skill detection?**
A block is currently a skill iff its `<FBNetwork>` instantiates
`<FB Type="BasicSKILL"/>`. Changing that changes what the tool is, so say why
if this proposal depends on it.

**Additional context**
Links to the IEC 61499 specification, the ontology, or to how
[PLC2Skill](https://github.com/hsu-aut/PLC2Skill) handles the equivalent case.
