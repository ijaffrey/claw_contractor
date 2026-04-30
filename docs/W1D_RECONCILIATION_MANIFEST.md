# W1-D Reconciliation Manifest

**Purpose:** Document the canonical version of every duplicated module in `claw_contractor`, so Phase 1 of the W1-D sprint can rewrite imports unambiguously.

**Scope:** Duplicate forks identified during W1-D Day 1 inspection. Files stay at their declared "winner" path — this manifest does NOT move files into a new package layout (that decision is deferred per ADR-001).

**Process for each pair:**
1. Identify all known versions
2. Declare a winner with rationale
3. List the loser(s) to be deleted
4. Specify the import-rewrite rule that points all callers at the winner

---

## How to read this manifest

Each entry has the structure:

> **Pair:** brief name
>
> **Versions found:**
> - path 1 (size, brief description)
> - path 2 (size, brief description)
>
> **Winner:** path
>
> **Rationale:** why this version
>
> **Losers (to delete):**
> - path
>
> **Import rewrites:**
> - `from foo import X` → `from bar import X`

---

## Pair 1: `database` module

**Versions found:**

- `./database.py` — 490 lines, 14 importers. Defines `Base`, `Lead`, `NotificationLog`, `UserToken`, `LeadStatus`, `NotificationType`, `NotificationStatus`, session management (`create_database_engine`, `get_db_session`, `init_database`, `DatabaseSession`), repositories (`LeadRepository`, `NotificationRepository`), and migration helpers.
- `./database_manager.py` — 301 lines, 4 importers. Defines a `DatabaseManager` class plus two module-level functions (`store_lead`, `get_conversation_state`).

**Winner:** `./database.py`

**Rationale:**

`database.py` is the actual production database layer. It defines the real models in use (`Lead`, `NotificationLog`, `UserToken`), has a working session management system, and is imported by 14 files including production code paths.

`database_manager.py` is broken in a way that has been masked by silent failure. Its imports look like this:

```python
try:
    from database import Base, User, Transaction, Account
except ImportError:
    Base = User = Transaction = Account = None
```

The classes `User`, `Transaction`, and `Account` **do not exist** in `database.py`. The `try/except` silently catches the `ImportError`, leaving `Base = None`. The class then proceeds to call `Base.metadata.create_all(self.engine)` on instantiation, which crashes with `AttributeError: 'NoneType' object has no attribute 'metadata'`.

In other words: the file has never been used in any code path that actually instantiates `DatabaseManager`. It exists as a phantom dependency. Its `DatabaseManager` class needs to be reconciled with the real database layer.

**Losers (to delete):**

- `./database_manager.py`

**Import rewrites:**

The four files importing from `database_manager.py` need their imports rewritten. The current `DatabaseManager` API (constructor, methods used by callers) needs to be inspected before rewriting — there are two paths:

- **Path A (preferred if API matches):** Add a `DatabaseManager` class to `database.py` that wraps the existing `LeadRepository` and `NotificationRepository`, exposing the methods the callers expect. Then rewrite imports:
  - `from database_manager import DatabaseManager` → `from database import DatabaseManager`
  - `import database_manager` → (replace usages with `from database import DatabaseManager` or whatever specific symbols are needed)

- **Path B (if API doesn't match):** Refactor the four callers to use `LeadRepository` / `NotificationRepository` directly. More work, but cleaner.

**Day 2 inspection task:** Read each of the four importers (`contractor_notifier.py`, `lead_summarizer.py`, `notification_manager.py`, `main.py`) to determine which path is appropriate.

**Also resolves:**

The phantom import `from src.database.database_manager import DatabaseManager` in `tests/test_conversation_manager.py` (line 9). The path `src/database/database_manager.py` does not exist anywhere in the repo. This test has been broken since it was written. After Pair 1 is reconciled, rewrite this import to `from database import DatabaseManager`.

---

## Pair 2: `conversation_manager`

**Versions found:**

- `./conversation_manager.py` — 3,975 bytes (~ 100 lines), defines a single `ConversationManager` class. Stub-level implementation: "Manages conversation state tracking and qualification flow logic."
- `./src/conversation_manager.py` — 21,008 bytes (~ 530 lines), defines a single `ConversationManager` class. Full implementation with database integration, message history, qualification state.

**Winner:** `./src/conversation_manager.py`

**Rationale:**

Both files have the same class name and same conceptual purpose. The `src/` version is 5x larger, has a complete implementation, integrates with the database, and uses the qualification manager. The root version reads as an early stub that was never deleted when the work moved into `src/`.

**Losers (to delete):**

- `./conversation_manager.py`

**Import rewrites:**

- `from conversation_manager import ConversationManager` → `from src.conversation_manager import ConversationManager`
- `import conversation_manager` → `from src import conversation_manager`

**Note on the `src/` version's own broken imports:**

The `src/conversation_manager.py` winner has its own broken import on line 5:

```python
from database import Database
```

There is no `Database` class in `database.py` — only `Base`, models, repositories, and session helpers. This is a Phase 1 escalation. Likely fix: change to `from database import Base` or `from database import get_db_session`, depending on what the code actually uses.

---

## Pair 3: `notification_service`

**Versions found:**

- `./app/services/notification_service.py` — 18,096 bytes. Older notification service implementation.
- `./src/services/notification_service.py` — 23,660 bytes. Defines `NotificationType` (Enum), `NotificationStatus` (Enum), `NotificationData`, `LeadSummary`, `NotificationService`. Includes full SMTP, MIME, error handling.

**Winner:** `./src/services/notification_service.py`

**Rationale:**

The `src/` version is larger, has a complete public surface (5 declared classes vs. fewer in `app/`), and includes production-ready features like SMTP setup, MIME assembly, and structured error handling. The `app/` version appears to be an older draft.

**Losers (to delete):**

- `./app/services/notification_service.py`

**Import rewrites:**

- `from app.services.notification_service import ...` → `from src.services.notification_service import ...`
- `from app.services import notification_service` → `from src.services import notification_service`

---

## Pair 4: `notification_log` model

**Versions found:**

- `./models/NotificationLog.py` — 1,874 bytes. Capitalized filename (non-PEP8). Imports `from src.database.base import Base` (broken — `src/database/` doesn't exist).
- `./app/models/notification_log.py` — exists per directory listing; size and content not yet inspected.
- `./src/models/notification_log.py` — 3,207 bytes. Has `NotificationTypeEnum` enum, uses `from ..database.base import Base` (relative import, also broken).

**Winner:** `./src/models/notification_log.py`

**Rationale:**

The `src/` version is the most complete (has its own enum, more attributes). It also has the standard PEP8 filename (`notification_log.py` not `NotificationLog.py`). The root-level `models/NotificationLog.py` and the `app/models/notification_log.py` appear to be earlier drafts that were superseded.

**Losers (to delete):**

- `./models/NotificationLog.py`
- `./app/models/notification_log.py`

**Import rewrites:**

- `from models.NotificationLog import NotificationLog` → `from src.models.notification_log import NotificationLog`
- `from app.models.notification_log import ...` → `from src.models.notification_log import ...`

**Note on the `src/` version's own broken imports:**

Both `src/models/notification_log.py` and `models/NotificationLog.py` import `Base` from `src.database.base` or `..database.base`. Neither path exists. The actual `Base` is defined in `database.py` at the repo root. Fix as part of Phase 1: change to `from database import Base`.

This is a recurring pattern (see Pair 2 also): many `src/` files were written assuming a `src/database/` package that was never built.

---

## Pair 5: `handoff` services

**Versions found:**

- `./src/services/handoff_service.py` — 30,896 bytes. Defines `LeadStatus` (Enum), `HandoffEventType` (Enum), `MessageTemplate`, `HandoffService`.
- `./src/workflows/handoff_workflow.py` — 17,608 bytes. Defines `HandoffResult`, `HandoffWorkflow`.
- `./src/services/lead_handoff_service.py` — exists in inventory; not yet inspected.

**Winner:** Both files survive — they are complementary, not duplicates.

**Rationale:**

`HandoffService` (in `src/services/handoff_service.py`) appears to be the lower-level service handling individual handoff operations. `HandoffWorkflow` (in `src/workflows/handoff_workflow.py`) appears to be the higher-level orchestrator that uses the service.

The third file, `src/services/lead_handoff_service.py`, needs Day 2 inspection to determine whether it's a third complementary piece or a fourth duplicate.

**Losers (to delete):**

- TBD pending Day 2 inspection of `src/services/lead_handoff_service.py`

**Import rewrites:**

- None for the two confirmed survivors — they keep their current paths.

**Day 2 inspection task:**

```bash
{
  echo "=== src/services/lead_handoff_service.py ==="
  wc -l src/services/lead_handoff_service.py
  grep -n "^class\|^def\|^async def" src/services/lead_handoff_service.py
  echo ""
  echo "=== Who imports from any handoff* module? ==="
  grep -rn "handoff" --include="*.py" --exclude-dir=venv --exclude-dir=.git . | head -30
}
```

---

## Pair 6: `email_templates`

**Versions found:**

- `./src/utils/email_templates.py` — 27,421 bytes (830 lines). Defines `contractor_notification_template` and other template functions. **Currently corrupted:** `SyntaxError: unterminated triple-quoted f-string literal (detected at line 831)`.
- One importer: `./contractor_notifier.py` (calls `self._load_email_templates()` and uses `self.email_templates[...]` dict-style — likely loads templates by name, not by importing the module directly).

**Winner:** `./src/utils/email_templates.py` (after repair)

**Rationale:**

Only one production file references email templates, and it does so via a `_load_email_templates()` method (suggesting the templates are loaded by name from this module). The file has a syntax error near line 670 (unterminated f-string) that prevents it from being imported at all.

This is the corruption case from the W1-D brief. It needs repair, not replacement. Estimated effort: ~15 minutes to find and close the unterminated triple-quoted string.

**Losers (to delete):**

- None.

**Phase 2 task (repair):**

1. Open `src/utils/email_templates.py`
2. Navigate to line 670 (where `html_content = f"""` opens)
3. Find where the f-string was supposed to close (likely a few hundred lines down, before the next function definition)
4. Add the closing `"""` at the correct location
5. Run `python3 -c "import ast; ast.parse(open('src/utils/email_templates.py').read())"` to verify syntax is valid
6. Verify `contractor_notifier.py` can still load templates after repair

If the file is genuinely unrecoverable (e.g., content was lost mid-write, not just an unterminated quote), the fallback is:
- Stub each template function to return placeholder HTML/text
- Mark with TODO comments
- File a follow-up task to rebuild the templates from production examples

**Phase 1 task (independent of repair):**

The file's existence at `src/utils/email_templates.py` is the canonical path. No import rewrites needed — `contractor_notifier.py` already references it correctly via its own internal loading mechanism.

---

## Pair 7: Empty speculative directories

**Versions found:**

- `./backend/` — 0 Python files
- `./lead_management/` — 0 Python files
- `./messaging/` — 0 Python files

**Winner:** None — these directories should be deleted.

**Rationale:**

Multiple files in the repo have imports like `from lead_management.contractor_notifier import ...` and `from messaging.email_sender import ...`. The directories these reference are empty. The actual modules exist at the repo root (e.g., `./contractor_notifier.py`).

These are pure phantom imports — the prefix should be stripped, leaving the real module name.

**Losers (to delete):**

- `./backend/` (after confirming empty)
- `./lead_management/` (after confirming empty)
- `./messaging/` (after confirming empty)

**Import rewrites:**

- `from lead_management.contractor_notifier import X` → `from contractor_notifier import X`
- `from lead_management.email_sender import X` → `from email_sender import X`
- `from messaging.notification_manager import X` → `from notification_manager import X`
- `from backend.<anything>` → strip `backend.` prefix
- `from messaging.<anything>` → strip `messaging.` prefix
- `from lead_management.<anything>` → strip `lead_management.` prefix

These are mechanical regex rewrites — they have unambiguous targets.

---

## Pair 8: Other suspected drift (Day 2 inspection)

The following pairs were identified in inventory but not yet fully inspected. Day 2 work to determine winners:

- `./services/` (root-level) vs. `./src/services/` — what's at root?
- `./routes/` (root-level) vs. `./app/routes/` — same routes, different versions?
- `./models/` (root-level) vs. `./app/models/` vs. `./src/models/` — beyond `notification_log`, what else lives here?

**Day 2 inspection task** (from earlier message, still pending):

```bash
{
  echo "=== Root-level services/ ==="
  ls -la services/ 2>/dev/null
  for f in services/*.py; do
    echo "--- $f ---"
    grep -n "^class\|^def\|^async def" "$f"
  done
  echo ""
  echo "=== Root-level routes/ ==="
  ls -la routes/ 2>/dev/null
  for f in routes/*.py; do
    echo "--- $f ---"
    grep -n "^class\|^def\|^async def" "$f"
  done
  echo ""
  echo "=== Root-level models/ ==="
  ls -la models/ 2>/dev/null
  for f in models/*.py; do
    echo "--- $f ---"
    grep -n "^class\|^def\|^async def" "$f"
  done
}
```

Once that runs, this manifest gets a Pair 8a, 8b, 8c with the same winner-loser-rewrite structure.

---

## Summary of decisions so far

| Pair | Winner | Losers | Status |
|------|--------|--------|--------|
| 1. database | `./database.py` | `./database_manager.py` | Decided. Day 2: choose Path A vs B for `DatabaseManager` API |
| 2. conversation_manager | `./src/conversation_manager.py` | `./conversation_manager.py` | Decided. Phase 1: also fix `from database import Database` |
| 3. notification_service | `./src/services/notification_service.py` | `./app/services/notification_service.py` | Decided |
| 4. notification_log | `./src/models/notification_log.py` | `./models/NotificationLog.py`, `./app/models/notification_log.py` | Decided. Phase 1: also fix `Base` import |
| 5. handoff | both `handoff_service.py` and `handoff_workflow.py` | TBD | Pending Day 2 inspection of `lead_handoff_service.py` |
| 6. email_templates | `./src/utils/email_templates.py` (repair) | none | Decided. Phase 2: repair syntax error |
| 7. speculative dirs | none | `./backend/`, `./lead_management/`, `./messaging/` | Decided. Mechanical rewrites |
| 8. services/routes/models | TBD | TBD | Day 2 inspection required |

## Order of operations in Phase 1

1. Run the Day 2 inspections (Pair 5 and Pair 8) and update this manifest with their results
2. For each decided pair, in order:
   - Delete the loser files
   - Run the import rewrites (sed or manual edit)
   - Run `pytest --collect-only` after each pair to confirm no new errors introduced
3. After all pairs are reconciled, run `pytest --collect-only` and confirm error count drops from 15+ to 0–3
4. Remaining errors are escalation cases for Phase 1 review (e.g., missing symbols that need stubbing or full implementation)

## Recurring fixes that span multiple pairs

These come up repeatedly in the manifest above and should be applied as a single sweep, separate from per-pair work:

1. **Phantom `src/database/` imports.** Multiple files import from `src.database.base` or `..database.base`. Rewrite all of these to `from database import Base`.
2. **Phantom class imports from `database`.** Multiple files import classes that don't exist in `database.py` (e.g., `Database`, `User`, `Transaction`, `Account`). Each needs case-by-case resolution — either rewrite to use existing classes (`Base`, `LeadRepository`) or stub the missing class.
3. **Capital-N filename violations.** `models/NotificationLog.py` and any other capitalized filenames violate PEP8. After deletion (Pair 4), confirm no other capitalized `.py` files remain.

---

## Sign-off

Manifest authored: 2026-04-29 by Ian / Claude during W1-D Day 1.

Manifest is provisional pending Day 2 inspections of Pair 5 and Pair 8.

Updates to this manifest after Day 2 inspections should be made in-place with a revision note in this section.


---

# Day 2 Inspection Results

Inspection performed: 2026-04-29 by Ian / Claude during W1-D Day 2.

## Pair 5 — Handoff trio inspection

**Files found (9 total handoff-related):**

| Path | Disposition |
|---|---|
| `src/services/handoff_service.py` | Day 1 winner — repository pattern, exception types |
| `src/workflows/handoff_workflow.py` | Day 1 winner — orchestrator, calls qualification + notification + lead services |
| `src/services/lead_handoff_service.py` | **Architectural escalation** — third orchestration layer, distinct decomposition |
| `services/LeadHandoffService.py` | **Architectural escalation** — root-level fork, repository-pattern variant (NOT same code as src/) |
| `lead_handoff.py` | **Phase 1 escalation** — root orphan, referenced by `notification_manager.py:543` |
| `customer_handoff_messenger.py` | Not yet inspected — out of scope for Pair 5 |
| `routes/handoff_routes.py` | **Architectural escalation** — sole copy, no `src/routes/` exists |
| `test_customer_handoff.py` | Test, fails on phantom `models.lead` import |
| `test_final_handoff_integration.py` | Test, fails on phantom `app.database` import |
| `tests/test_handoff_workflow.py` | Test, fails on phantom `claw_contractor` import |

**Verdict on `lead_handoff_service.py`:** Functionally distinct from both Day 1 winners. Defines its own `HandoffStatus` enum, `QualificationCriteria` (evidence-based vs. score-based), `LeadSummary` dataclass. Calls 5 sibling services directly rather than going through repositories. **This is a competing design, not a duplicate.** Marked as architectural escalation pending Phase 1 review. No deletion in W1-D.

## Pair 8 — Root-level services/routes/models inspection

**Findings:**

| File | Verdict | Action |
|---|---|---|
| `models/NotificationLog.py` | Confirmed loser — folds into Pair 4 (CapitalCase, redundant with `src/models/notification_log.py`) | Delete in Pair 4 reconciliation |
| `services/NotificationService.py` | **Architectural escalation** — distinct from `src/services/notification_service.py`. Root version is sync-only (smtplib), src version is async-capable (aiosmtplib + asyncio), uses db session injection, has `NotificationType` enum | Keep, defer |
| `services/LeadHandoffService.py` | **Architectural escalation** — distinct from `src/services/lead_handoff_service.py` (repository pattern vs. service-orchestration pattern, score-based vs. evidence-based qualification) | Keep, defer |
| `routes/handoff_routes.py` | **Phase 1 escalation** — sole copy of route definitions; no `src/routes/` directory exists | Keep, defer |

**Reframing:** Pair 8 is not a single pair. It is one confirmed loser folding into Pair 4 plus three architectural escalations. The root-level `services/`, `routes/`, `models/` directories cannot be deleted en bloc.

**Import surface from root-level dirs:** Only 2 files reference them, and both imports are already broken:
- `test_customer_handoff.py:12` imports `from models.lead import Lead` (file does not exist)
- `test_main_integration.py:12` imports `from models import Base, Email, Lead, Conversation, QualifiedLead, User, Client` (no `__init__.py` exposing these)

These broken imports will be addressed via skip markers (see "Skipped tests registry" below).

## Pytest baseline (Day 2 start)

Captured before any Day 2 reconciliation work. Saved at `/tmp/pytest_baseline_day2.txt` on the build host.

- **Errors during collection:** 15
- **Tests collected despite errors:** 23

Error attribution to pairs:

| Pair | Error count | Test files |
|---|---|---|
| Pair 1 (database imports) | 3 | `test_notification_logger.py`, `test_qualified_lead_handler.py`, `tests/test_conversation_manager.py` |
| Pair 7 (phantom backend/lead_management/messaging) | 3 | `test_contractor_notifier.py`, `test_customer_handoff.py`, `tests/test_notification_service.py` |
| Phantom src/ and app/ namespaces | 4 | `test_email_sender.py`, `test_final_handoff_integration.py`, `test_notification_manager.py`, `test_qualified_lead_detector.py` |
| Self-reference (`claw_contractor` package) | 1 | `tests/test_handoff_workflow.py` |
| Schema gap (`Conversations` symbol) | 1 | `test_conversations_table.py` |
| Missing symbol (`main_loop`) | 1 | `test_main_integration.py` |
| Config attribute (`GMAIL_USER_EMAIL`) | 1 | `test_poll.py` |
| Syntax error (corrupted file) | 1 | `test_e2e.py` (line 741, unterminated string) |

## Architectural escalations queue (for Phase 1)

The following decisions are explicitly deferred per ADR-001. They surface as Phase 1 work items:

1. **Lead handoff orchestrator.** Pick winner among `src/services/lead_handoff_service.py`, `services/LeadHandoffService.py`, and `src/workflows/handoff_workflow.py`. Three distinct designs for the same concept.
2. **Notification service architecture.** `services/NotificationService.py` (sync, smtplib, env-vars) vs. `src/services/notification_service.py` (async, aiosmtplib, db session, settings injection). Pick one paradigm.
3. **Routes namespace.** `routes/handoff_routes.py` is the sole copy of any route definitions. Decide: relocate to `src/routes/` (creating the dir), keep at root, or move into `src/api/`.
4. **Root orphan: `lead_handoff.py`.** Used by `notification_manager.py:543`. Decide: fold into chosen handoff orchestrator, stub for compatibility, or delete with `notification_manager` rewrite.
5. **Tests-at-root vs `tests/` directory.** Twelve test files at repo root, three in `tests/`. Consolidate.

## Skipped tests registry (W1-D Phase 2 will add markers)

The following tests will be marked `pytest.skip` with a `reason=` pointing to the architectural escalation they depend on. This unblocks CI without forcing premature architectural decisions.

| Test file | Skip reason | Blocked on escalation |
|---|---|---|
| `test_customer_handoff.py` | Imports `models.lead`, `models.contractor` (phantom) | #1, #5 |
| `test_final_handoff_integration.py` | Imports `app.database` (phantom) | #1 |
| `tests/test_handoff_workflow.py` | Imports `claw_contractor` (self-package, not installed) | #1 |
| `tests/test_notification_service.py` | Imports `backend` (phantom) | #2 |
| `test_email_sender.py` | Imports `src.email_sender` (phantom) | Schema gap |
| `test_notification_manager.py` | Imports `src.notification_manager` (phantom) | #2 |
| `test_qualified_lead_detector.py` | Imports `app.modules` (phantom) | Schema gap |
| `test_main_integration.py` | Imports `main_loop` (missing symbol) | Schema gap |
| `test_conversations_table.py` | Imports `Conversations` (missing symbol) | Schema gap |
| `test_e2e.py` | Syntax error line 741 (unterminated string) | Phase 2 file repair |
| `test_poll.py` | Missing config attribute `Config.GMAIL_USER_EMAIL` | Phase 2 config repair |

## Updated Pair-by-Pair Summary (post-Day 2)

| Pair | Winner | Losers | Status |
|---|---|---|---|
| 1. database | `./database.py` | `./database_manager.py` | Decided. Path A vs B for `DatabaseManager` API to be selected during reconciliation |
| 2. conversation_manager | `./src/conversation_manager.py` | `./conversation_manager.py` | Decided |
| 3. notification_service | `./src/services/notification_service.py` | `./app/services/notification_service.py`, **root fork deferred — see escalation #2** | Day 1 plan stands; root fork escalated |
| 4. notification_log | `./src/models/notification_log.py` | `./models/NotificationLog.py`, `./app/models/notification_log.py` | Decided. Confirmed Day 2 |
| 5. handoff trio | `src/services/handoff_service.py`, `src/workflows/handoff_workflow.py` | None deleted in W1-D — `lead_handoff_service.py` and friends escalated | See escalation #1 |
| 6. email_templates | `./src/utils/email_templates.py` (repair) | None | Phase 2 syntax repair |
| 7. speculative dirs | None | `./backend/`, `./lead_management/`, `./messaging/` | Mechanical rewrites + phantom-import skip markers |
| 8. services/routes/models at root | `models/NotificationLog.py` folds into Pair 4 | Three escalations: see #1, #2, #3 | Reframed as one delete + three escalations |

## Sign-off (Day 2)

Day 2 inspections complete. Manifest is now final for W1-D scope. Architectural escalations recorded for Phase 1 follow-up.

Updated: 2026-04-29 by Ian / Claude during W1-D Day 2.
