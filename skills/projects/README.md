# Project-Local Skills

This directory holds skills scoped to a single governed project. Each project lives in its own subdirectory; each skill within a project lives in its own folder with a `SKILL.md` and any helper scripts.

```
skills/projects/
  <project-name>/
    <skill-name>/
      SKILL.md
      <optional helpers>
```

Project-local skills follow the same canonical contract as global skills (`SKILL.md` frontmatter with `targets`, body, optional helpers). They are synced to host-native surfaces by the same renderers in `scripts/omni_factory.py`.

## Adding a project

Run `scripts/bootstrap-project.sh <project-name>` to scaffold a governed project. The bootstrap appends an entry to `projects.json` and creates the project tree.

After scaffolding, add skills under `skills/projects/<project-name>/<skill-name>/` and run the sync engine to deliver them to Claude, Codex, and Gemini.

## See also

- The `onboarding-guide` skill (`skills/global/onboarding-guide/`) walks first-time operators through what gets installed and how to register their first project.
- `docs/CONOPS.md` § Capability Model describes the canonical authoring contract.
- `docs/QUICKSTART.md` lists the end-to-end first-run flow.
