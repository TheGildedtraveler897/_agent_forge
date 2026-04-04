---
description: Audit Jarvis dependencies, bootstrap gaps, and doctrine drift
---

Run a Jarvis dependency and doctrine audit.

Check:
1. imported packages versus declared requirements
2. missing bootstrap or setup helpers
3. hardcoded absolute paths
4. hardcoded secrets or URLs
5. accidental `.env` tracking

Report findings first, propose exact fixes, and wait for approval before changing files.
