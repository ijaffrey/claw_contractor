# Contributing to claw_contractor

This document defines conventions for contributing to this repository. It deliberately does NOT prescribe directory structure — that decision is captured in [`docs/adr/ADR-001-repo-structure.md`](docs/adr/ADR-001-repo-structure.md) and is currently deferred. Conventions here apply regardless of how the repo is eventually structured.

These conventions are designed to be portable. They are intended to become the **Patrick Agent Project Standard** — the baseline conventions every agent the Agent Factory produces should follow.

---

## 1. Python version

Python 3.11+. All code is written assuming f-strings, walrus operators, and PEP 604 union syntax (`int | None`) are available.

When invoking Python from the shell, always use `python3` explicitly. Never use bare `python` — on some macOS setups it resolves to Python 2.

---

## 2. Code style

### Formatting

`black` with default settings is the formatter of record. Configuration in `pyproject.toml`:

```toml
[tool.black]
line-length = 88
target-version = ["py311"]
```

Run before every commit:

```bash
black .
```

CI fails on `black --check` differences. There is no negotiation on formatting style — `black` decides.

### Linting

`flake8` with the configuration in `.flake8`:

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = venv,.venv,build,dist,*.egg-info
```

`E203` and `W503` are ignored because they conflict with `black`. CI fails on any other flake8 error.

### Imports

- Standard library imports first
- Third-party imports second
- Local imports third
- Each group separated by a blank line
- Within a group, alphabetical

`isort --profile black` enforces this. Optional but recommended in pre-commit.

---

## 3. Testing

### Test discovery

`pytest` is the test runner. Tests live in either:
- `tests/` (preferred for new code)
- `test_*.py` at the location of the code being tested (acceptable for legacy)

`pytest.ini` or `pyproject.toml` configures discovery:

```toml
[tool.pytest.ini_options]
testpaths = ["tests", "."]
python_files = ["test_*.py"]
```

### Test gates

Two gates must pass before any PR is mergeable:

1. **`pytest --collect-only`** must succeed with zero errors. This is the minimum bar — tests must at least be discoverable and importable. A test that cannot be collected is worse than a missing test, because it gives false confidence.
2. **`pytest`** (full run) must pass. New code requires new tests.

CI enforces both. PRs that break collection are auto-rejected.

### Test naming

- Test files: `test_<module>.py`
- Test functions: `test_<behavior>_<condition>` (e.g., `test_create_lead_returns_id_when_valid`)
- Test classes (if used): `Test<Subject>` (e.g., `TestLeadRepository`)

### Test isolation

- No test should depend on another test's side effects
- Database tests use a transaction-rollback fixture or an in-memory SQLite instance, never the production DB
- External services (SMTP, Stripe, etc.) are mocked, not invoked
- Any test that touches the network without mocking must be marked `@pytest.mark.integration` and excluded from the default test run

---

## 4. Commits

### Commit message format

```
<type>: <short summary, lowercase, no period>

<optional body, wrapped at 72 chars>

<optional footer with refs/issues>
```

Types:
- `feat` — new feature
- `fix` — bug fix
- `chore` — maintenance, dependency bumps, formatting
- `ci` — CI configuration changes
- `docs` — documentation only
- `refactor` — code change that neither fixes a bug nor adds a feature
- `test` — adding or fixing tests

Examples:
```
feat: add lead enrichment via Clearbit API
fix: handle SQLAlchemy 2.x Row keys in campaign CRUD
chore: bump black to 24.3.0
docs: ADR-001 defer repo structure decision
```

### Atomic commits

One logical change per commit. If a commit message has "and" in it, it should probably be two commits.

### Commit cadence

Commit at every meaningful checkpoint. Push at least once per session. Long-lived uncommitted changes are a liability.

### Never commit

- Secrets (API keys, tokens, passwords) — use environment variables
- Generated files (build artifacts, cache directories, virtualenvs)
- IDE configuration that's user-specific (`.vscode/settings.json` for personal settings)
- Large binaries — use Git LFS or external storage

`.gitignore` should be the first thing checked when something feels off. If a file shouldn't be in the repo, ignore it before committing.

---

## 5. Branches

### Branch naming

```
<type>/<short-description>
```

Types match commit types. Examples:
```
feat/clearbit-enrichment
fix/sqlalchemy-2x-row-keys
ci/black-and-upload-artifact-v4
chore/triage-quarantined-files
docs/adr-001-repo-structure
```

Avoid:
- Branch names with usernames (`ian/feature-x`)
- Branch names with dates only (`branch-2026-04-29`)
- Generic names (`update`, `wip`, `test`)

### Branch lifecycle

- One branch per logical unit of work
- Branches merge into `main` via PR
- Delete merged branches (locally and on origin)
- Stale branches (no activity for 30+ days) get archived or deleted

---

## 6. Pull requests

### PR title format

Same as commit message format.

### PR description template

```markdown
## What

Brief description of the change.

## Why

Context — what problem does this solve?

## How to verify

Steps a reviewer can run to confirm the change works.

## Risk

What could go wrong? What's the rollback plan?

## Related

Links to issues, ADRs, prior PRs, or external docs.
```

### PR size

Smaller PRs review faster and merge faster. Target:
- < 400 lines diff for a typical PR
- < 1000 lines for a substantial feature
- > 1000 lines should be split, or have a written justification in the description

### PR gates

Before requesting review, all of these must be green:

- [ ] `black --check` passes
- [ ] `flake8` passes
- [ ] `pytest --collect-only` passes
- [ ] `pytest` passes
- [ ] CI workflow runs to completion
- [ ] PR description is filled out

---

## 7. Pre-commit hooks

`.pre-commit-config.yaml` runs the formatting and lint gates locally before commits land:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]
```

Install once per clone:

```bash
pip install pre-commit
pre-commit install
```

Pre-commit is **strongly recommended**. Without it, you'll discover formatting failures only when CI rejects your PR — slower and more annoying than a 2-second local hook.

---

## 8. Dependencies

### Adding a dependency

- Add to `requirements.txt` (or `pyproject.toml` `[project.dependencies]` if using PEP 621)
- Pin to a specific version: `requests==2.31.0`, not `requests>=2.31.0`
- Add a one-line comment explaining why if the purpose isn't obvious

### Updating a dependency

- One PR per dependency update for non-trivial bumps
- Run the full test suite locally before opening the PR
- Note in the PR description what changed and whether the API shifted

### Dev dependencies

`requirements-dev.txt` for tools used in development but not at runtime (`black`, `flake8`, `pytest`, `pre-commit`).

---

## 9. Documentation

### Module docstrings

Every Python file starts with a module docstring describing what it contains and why it exists:

```python
"""
Lead enrichment service.

Coordinates calls to external enrichment APIs (Clearbit, Hunter, Apollo)
and persists results to the leads table. Used by the bulk-enrich workflow
and the per-row enrichment button in the campaign dashboard.
"""
```

### Function docstrings

Public functions get docstrings. Use Google or NumPy style consistently within a module.

### README.md

The repo's `README.md` should answer:
- What does this project do?
- How do I run it locally?
- How do I run the tests?
- Where does production deploy from?
- Who owns it?

### Architecture decisions

Significant architectural decisions get an ADR in `docs/adr/`. Use the format:

```
docs/adr/NNNN-decision-name.md
```

Numbered sequentially. See `ADR-001-repo-structure.md` for the format.

---

## 10. Secrets and configuration

### Secrets never go in the repo

API keys, database passwords, tokens — all live in environment variables, loaded from a `.env` file that is `.gitignore`'d.

`.env.example` lives in the repo as a template, listing every variable the app needs with example/dummy values:

```
DATABASE_URL=postgres://user:pass@localhost/dbname
ANTHROPIC_API_KEY=sk-ant-xxx
GMAIL_USER_EMAIL=you@example.com
SENDGRID_API_KEY=SG.xxx
```

If you add a new secret, update `.env.example` in the same commit.

### Configuration loading

Use `os.getenv()` with explicit defaults at module import or app startup. Fail loudly if a required secret is missing — don't silently fall back.

```python
# Good
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

# Bad
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///prod_will_silently_use_this.db")
```

---

## 11. Working with Patrick

Patrick is the orchestration system that lands autonomous PRs into this repo. To make Patrick's work reviewable and safe:

### Patrick's PRs follow the same standards

Patrick's PRs go through the same gates as human PRs. No bypassing CI, no force-pushes to `main`, no skipping review for "automated" changes.

### Patrick's commits are atomic and descriptive

Each commit Patrick makes corresponds to one step in a sprint plan. Commit messages reference the sprint and step:

```
sprint-c3: step 4 — proposal generator (skipp + drafted brands)
```

### Patrick announces structural changes

Anything that moves files, renames modules, or changes import paths is flagged in the PR description as a structural change. Reviewers know to look for downstream import breakage.

### Patrick respects the ADR

If a sprint would touch a question that's been deferred in an ADR (e.g., directory structure, ADR-001), Patrick stops and escalates rather than choosing a default.

---

## Appendix: Why this document exists

This file was created during the W1-D Contractor AI Repair Sprint (April 2026), as part of stabilizing the repo after a period of rapid feature development that produced inconsistent conventions across files.

The conventions documented here describe what we've decided going forward. Existing code that doesn't yet match these conventions will be brought into compliance incrementally as it's touched, not in a single sweep.

Questions, disputes, or proposed changes to these conventions should go through a PR against this file.
