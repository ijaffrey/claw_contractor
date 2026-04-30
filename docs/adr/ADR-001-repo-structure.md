# ADR-001: Repository Structure — Decision Deferred

**Status:** Deferred
**Date:** 2026-04-29
**Sprint:** W1-D — Contractor AI Repair
**Decision owner:** Ian
**Reviewers:** Patrick (orchestrator)

---

## Context

The `claw_contractor` repository was originally scaffolded as the home of a single product — Contractor AI, a lead capture and qualification system. Over multiple sprints (A through G1, plus C3 integration and E3 UX), it grew to contain code for what now appears to be **at least 4–5 distinct products**:

- The original Contractor AI lead capture and qualification system (sprints A, B, C, C3)
- A DOB permit puller and Manhattan permit scanner (sprints A, D)
- A self-serve RFP portal for architects (sprint D2)
- A bid-sourcing system with notifications and scheduler (sprint D3)
- A contractor portal frontend (sprints E, E2, E3)
- An NYC expansion module (sprint G1)

This growth happened organically without an explicit architectural decision about whether the repo should be:
- A single product (Contractor AI) with the other features as sub-modules
- A monorepo for a Skipp construction-tech product family
- A staging area to be split into multiple repos as products mature

The W1-D sprint inspection (April 29, 2026) surfaced the consequences of this undeclared structure:

- **122 Python files** spread across 22 directories
- **At least 6 organizational schemes** mixed in the same tree (root-level modules, `app/`, `src/`, `services/`, `routes/`, `models/`, `infrastructure/`)
- **Divergent forks of the same module** at multiple paths — for example, `conversation_manager.py` (4KB stub at root) and `src/conversation_manager.py` (21KB full implementation), and `notification_service.py` in both `app/services/` and `src/services/`
- **A broken `database_manager.py`** that imports nonexistent classes (`User`, `Transaction`, `Account`) and would crash on instantiation
- **Speculative directories** (`backend/`, `lead_management/`, `messaging/`) that are empty but referenced in import statements
- **15+ `pytest --collect-only` errors** stemming from these inconsistencies

The W1-D sprint brief originally proposed solving this by choosing a canonical directory structure (Phase 3) and migrating all code into it. After inspection, this approach was reconsidered.

## Why the decision is being deferred

The right structural decision depends on a strategic question that has not yet been answered:

> **Is `claw_contractor` one product, or is it the monorepo for the Skipp product family?**

This question is upstream of any directory layout. Choosing a layout before answering it would mean:

- **If we choose single-product layout (e.g., `src/contractor_ai/`)** but the repo is actually a multi-product monorepo: every non-Contractor-AI feature gets shoehorned into a Contractor AI namespace, perpetuating the entanglement we're trying to fix.
- **If we choose monorepo layout (e.g., `src/{contractor_ai,rfp_portal,permit_scanner,...}/`)** but we haven't decided what the product family is: we'd be guessing at boundaries that may turn out wrong, requiring another migration in 2–3 months.
- **If we choose to split into multiple repos** without a clear product family declaration: we'd lose history, fragment CI, and create coordination overhead before knowing whether the products genuinely belong apart.

The strategic question is not a sprint-deadline question. It belongs in a separate conversation about Skipp's product roadmap and how the Patrick Agent Factory should organize the products it spawns.

W1-D's actual goal — making the repo a place where Patrick can land clean autonomous PRs — does not require this decision to be made. It requires the existing code to be discoverable, importable, formatted, and CI-compliant. Those are tractable problems at the current directory layout.

## Options considered

### Option A — Flat root layout

Keep all runtime modules at the repo root. Tests in `tests/` or co-located `test_*.py`. No `src/` package layout.

**Pros:**
- Matches the current center of gravity (72 of 122 Python files are at root)
- Fastest path to green CI (Phase 1 import rewrites become mechanical)
- Lowest risk during W1-D — no file moves means no chance of breaking runtime paths
- Doesn't foreclose any future structural decision

**Cons:**
- Not `pip install`-able without future restructure
- Doesn't scale gracefully as the repo grows
- Root namespace becomes increasingly polluted

### Option B-classic — Single-product `src/` layout

Move all runtime modules into `src/contractor_ai/`. Standard Python packaging layout. `pyproject.toml` declares the package.

**Pros:**
- Standard Python packaging, `pip install -e .` works
- Clean import paths (`from contractor_ai.services import LeadQualifier`)
- Foundation for future MCP/npm distribution
- Matches the Patrick Agent Project Standard the rest of the Agent Factory should adopt

**Cons:**
- Forces a single-product shape on what is currently a multi-product reality
- Significant migration work (122 files moved, 100+ imports rewritten, reconciliation of duplicate forks)
- Risk of breaking runtime paths during migration
- Likely requires re-migration to monorepo layout when product separation becomes explicit

### Option B-mono — Monorepo `src/` layout

Move runtime modules into `src/{product_name}/` packages, with shared infrastructure (database, models, common utilities) in `src/skipp_core/` or similar:

```
src/
  contractor_ai/
  rfp_portal/
  permit_scanner/
  bid_sourcing/
  contractor_portal/
  skipp_core/
```

**Pros:**
- Reflects the multi-product reality
- Each product package can be independently developed, tested, and (eventually) extracted
- Shared infrastructure (database, models) lives in one canonical place
- Aligns with the long-term Agent Factory vision where Patrick spawns multiple products in one workspace

**Cons:**
- Requires deciding *now* what the product family is and which existing files belong to which product — a strategic decision that hasn't been made
- Largest migration scope (categorize every file by product, plus the moves and rewrites)
- If the product family decision later changes, the migration was wasted work
- `skipp_core` becomes a dumping ground if shared-vs-product boundaries aren't clear

### Option B-split — Multiple repositories

Split each product into its own repository. `claw_contractor` becomes Contractor AI only. `skipp_rfp_portal`, `skipp_permit_scanner`, etc. spin off as separate repos.

**Pros:**
- Cleanest separation of concerns
- Each product has independent release cadence, CI, and deployment
- Easier to open-source individual products later

**Cons:**
- Catastrophically disruptive in W1-D timeframe (estimated 2–3 weeks vs. 5 days)
- Loses git history continuity for moved code
- Requires coordination between repos for shared infrastructure (database schema, models)
- Premature if products haven't proven they belong apart

## Decision

**Defer the structural decision. For the duration of W1-D, work at the current (predominantly flat) layout. Do not migrate.**

Specifically:

1. The W1-D sprint will stabilize the repo — fix imports, reconcile duplicate forks, harden CI, clean branches — **without moving files into a new package layout**.
2. Duplicate forks will be resolved by declaring a winner per pair (see `docs/W1D_RECONCILIATION_MANIFEST.md`) and deleting the loser. Winners stay at their current paths.
3. The structural decision is captured in this ADR and revisited when one of the trigger conditions below is met.

## Trigger conditions for revisiting

This ADR should be revisited and a structural decision made when **any** of the following occurs:

- **Trigger 1: A 6th product is proposed.** If sprint H or beyond proposes another distinct product in this repo, the multi-product reality has solidified and B-mono should be seriously considered.
- **Trigger 2: A product needs `pip install` distribution.** If Contractor AI (or any product in this repo) needs to be installable as a Python package — e.g., to be consumed by another agent Patrick spawns — B-classic for that product becomes necessary.
- **Trigger 3: Two products start interfering with each other in production.** If a deployment of one product breaks another (e.g., conflicting dependencies, shared global state, namespace collisions), the products need physical separation, which means B-mono or B-split.
- **Trigger 4: The Skipp product family is formally declared.** If a strategic decision is made about which products belong under the Skipp brand and how they relate, the directory structure should reflect that decision and B-mono becomes the natural choice.
- **Trigger 5: Patrick's Agent Factory standard is formalized.** When the Patrick Agent Project Standard is codified for new agent scaffolding, the question of how multi-product agent monorepos should be organized must be answered — and this repo should be brought into line.

When a trigger fires, the next sprint should include explicit time for:
1. A strategic conversation about the underlying product question
2. A new ADR (ADR-002 or later) documenting the decision
3. A migration sprint to execute the structural change

## Consequences of deferral

### Accepted costs

- **The repo remains structurally messy** for some additional period. Imports stay at their current (sometimes awkward) paths. Speculative directories that are empty stay in the import map until imports are fixed.
- **Future migration is bigger than today's would have been**, because more sprint branches will have landed by then. Estimated to be 1–2x the size of doing it today.
- **The Patrick Agent Project Standard** can describe everything *except* the package layout. New agents Patrick scaffolds will need to make their own structural decision until ADR-002 lands.

### Avoided costs

- **No risk of choosing wrong now and re-migrating later.** A wrong choice today, applied to 122 files, would cost 2x the migration plus the cost of the wrong intermediate state.
- **No deadline pressure on a strategic question.** The structural decision gets the time it deserves rather than being forced by a sprint timeline.
- **W1-D ships in 5 days instead of 7+.** The migration was the biggest risk and time-sink in the original brief.

### Risks introduced by deferring

- **Risk:** "Defer" becomes "ignore," and the question never gets answered.
  - **Mitigation:** Trigger conditions above are explicit and observable. When any fires, this ADR is revisited.
- **Risk:** Patrick may scaffold a new agent in the same flat layout because there's no standard to follow.
  - **Mitigation:** CONTRIBUTING.md notes that new agents should make a structural decision at scaffold time. Patrick's planning prompts should reference this ADR when structural choices come up.
- **Risk:** A new contributor (or Patrick) makes ad-hoc structural choices that further fragment the layout.
  - **Mitigation:** All structural changes (file moves, new directories, package declarations) require either a PR-level discussion or a new ADR. This is enforced through PR review.

## Related documents

- `CONTRIBUTING.md` — conventions that apply regardless of structure
- `docs/W1D_RECONCILIATION_MANIFEST.md` — duplicate-fork resolutions for W1-D
- W1-D Sprint Plan v2 — the revised sprint that implements this deferral

## Revision history

| Date | Author | Change |
|------|--------|--------|
| 2026-04-29 | Ian / Claude | Initial ADR — decision deferred |
