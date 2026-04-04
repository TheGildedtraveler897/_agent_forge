---
description: Plan or execute the deterministic bootstrap of a new governed project under ~/Projects
argument-hint: <project-name> [--existing] [--skills]
---

Use the Agent Forge bootstrap flow for this project target:

$ARGUMENTS

Responsibilities:
- determine whether this is a new or existing project
- ensure the required governance files and `.claude` structure are present
- use the canonical bootstrap script for deterministic filesystem work
- explain post-bootstrap sync and verification steps

Default to the thinnest complete governance footprint unless the request clearly asks for project-local skills on day one.
