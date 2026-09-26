---
name: pixu-env-config
description: "Use when adding or changing Pixu configuration that should come from the environment, so settings are declared through .envs and concrete local values stay in the ignored .env."
---

# Pixu environment configuration

Apply this skill whenever a task adds, renames, removes, or changes a Django setting, Compose setting, integration credential, host/URL, feature flag, or other deploy-time value.

## Required convention

Every new deploy-time setting has three layers, in every environment:

1. The Django or application code reads a named environment variable. Keep the value out of Python, templates, JavaScript, and tracked documentation.
2. The appropriate file under `.envs/` declares the variable and redirects its value from the runtime environment using `${NAME}`. For local Compose, this normally means `.envs/.local/.django` or `.envs/.local/.postgres`; for production, `.envs/.production/.django` or `.envs/.production/.postgres`.
3. The concrete local value is configured only in the ignored root `.env` file. Do not add that value to a tracked `.envs` file.

Example:

```dotenv
# config/settings/base.py
DJANGO_ALLOW_URLS = env.list("DJANGO_ALLOW_URLS")

# .envs/.local/.django
DJANGO_ALLOW_URLS=${DJANGO_ALLOW_URLS}

# .env (ignored)
DJANGO_ALLOW_URLS=localhost
```

Use the project's existing `django-environ` naming and type parsing (`env`, `env.bool`, `env.int`, `env.list`) instead of inventing a second configuration mechanism. Keep the same variable name across code, `.envs`, Compose, and `.env`.

## Pixu-specific boundaries

- Read `AGENTS.md`, `PIXU_IMPLEMENTATION_BRIEF.md`, and the active OpenSpec change before editing configuration.
- Inspect the Compose `env_file` wiring before choosing the `.envs` file. The local stack currently loads `.envs/.local/.django`, `.envs/.local/.postgres`, and `.env`; production loads `.envs/.production/.django` and `.envs/.production/.postgres`.
- Production Compose consumes `.envs/.production/.django` and `.envs/.production/.postgres`; keep those runtime files ignored and use the same `${NAME}` bridge when their concrete values are supplied by the root `.env` or deployment secret injection. Keep only placeholders or bridge declarations in `.envs/.production/*.example`; never commit or print real production values.
- Never put passwords, tokens, app passwords, private keys, or real host credentials in a skill, tracked `.envs` file, example file, docs, tests, terminal output, or commit. Do not copy values from `.env` into source control.
- Prefer adding a new variable over hardcoding a default when the value differs by environment. A safe non-secret fallback is allowed only when the project convention and the setting's security impact make it appropriate.
- When renaming a variable, update the code, every relevant `.envs` declaration, examples, Compose wiring, and deployment documentation together; preserve a compatibility alias only if an approved migration requires it.

## Workflow

1. Search for the setting and its existing variable name before editing.
2. Add or update the typed environment read in the correct settings module.
3. Add the corresponding `${NAME}` declaration to the relevant `.envs` file. For production, mirror the declaration in the tracked `.example` and keep the real runtime file ignored.
4. Add the concrete local value only to `.env` when local execution needs it; never use shell output or documentation as a value store.
5. Verify Compose loads the intended files, run `git diff --check`, and run the smallest relevant Django check or test when requested by the task.
6. Review the diff for accidental secrets with `git diff -- .env .envs` and `git status --short`; do not print the contents of `.env`.
