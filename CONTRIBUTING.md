# Contributing
- Keep it **one file, local-first, AI-agnostic**. New features go in `offeros.py` with a test in `tests/`.
- Never add code that submits applications, logs in, scrapes job boards or messages people automatically. PRs that do will be closed (see `docs/COMPLIANCE.md`).
- New prompt? Add `prompts/<task>.md` using `{{CANDIDATE}}`, `{{JOB_CARD}}`, `{{JD_EXCERPT}}`, and register the task in `packet --task`.
- New skill? `skills/<name>/SKILL.md` with `name` + `description` frontmatter.
- Run `python -m pytest -q` before opening a PR.
