"""ContractorAI portal — Flask web UI for Nauman's bid pipeline.

Mobile-first. Reads pipeline artifacts directly from disk (scan_results/,
dob_output/, proposals/) so it can run alongside the existing CLI pipeline.
"""
from __future__ import annotations

import glob
import json
import os
import threading
import time
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    Response,
    abort,
    jsonify,
    render_template,
    request,
    send_file,
    stream_with_context,
    url_for,
)

from .pipeline_state import (
    STATE_PATH,
    load_state,
    save_state,
    set_address_state,
)
from .tier1_estimator import load_cache as load_tier1_cache, refresh_cache as refresh_tier1

# Repo root = parent of portal/
REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_RESULTS_DIR = REPO_ROOT / "scan_results"
DOB_OUTPUT_DIR = REPO_ROOT / "dob_output"
PROPOSALS_DIR = REPO_ROOT / "proposals"


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )

    # ------------------------------------------------------------------
    # sidebar context processor
    # ------------------------------------------------------------------
    BUCKET_LABELS = {
        "Abatement": "Abatement",
        "Concrete": "Concrete",
        "Demo": "Demolition",
        "GC_opportunity": "General Contractor",
        "Kitchen": "Kitchen",
        "Roofing": "Roofing",
        "Sitework": "Sitework",
    }

    @app.context_processor
    def inject_sidebar():
        scan = _latest_scan()
        buckets = []
        for b in scan.get("buckets", []):
            name = b.get("bucket", "")
            raw = b.get("count_raw") or 0
            buckets.append({
                "name": name,
                "label": BUCKET_LABELS.get(name, name),
                "count": raw if raw else None,
            })
        return {"sidebar_buckets": buckets, "active_page": ""}

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _latest_scan() -> dict[str, Any]:
        """Load the most recent scan_analysis_v2_*.json."""
        if not SCAN_RESULTS_DIR.exists():
            return {}
        candidates = sorted(
            SCAN_RESULTS_DIR.glob("scan_analysis_v2_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            return {}
        with open(candidates[0]) as f:
            return json.load(f)

    def _slugify_address(address: str) -> str:
        s = address.lower().strip()
        for ch in [",", ".", "'", '"']:
            s = s.replace(ch, "")
        return "_".join(s.split())

    def _load_takeoff(slug: str) -> dict[str, Any] | None:
        path = DOB_OUTPUT_DIR / slug / "takeoff.json"
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    def _find_drip_schedule(slug: str) -> Path | None:
        matches = list(PROPOSALS_DIR.glob(f"{slug}_*_drip_schedule.json"))
        return matches[0] if matches else None

    def _find_proposal_pdf(slug: str) -> Path | None:
        matches = [
            p
            for p in PROPOSALS_DIR.glob(f"{slug}_*_proposal.pdf")
        ]
        return matches[0] if matches else None

    # ------------------------------------------------------------------
    # routes
    # ------------------------------------------------------------------
    @app.route("/")
    def dashboard():
        scan = _latest_scan()
        buckets_raw = scan.get("buckets", [])
        total_permits = scan.get("permits_fetched", 0)
        state = load_state()
        generated_count = sum(
            1
            for v in state.get("addresses", {}).values()
            if v.get("status") == "generated"
        )
        sent_count = sum(
            1
            for v in state.get("addresses", {}).values()
            if v.get("status") == "sent"
        )

        # Tier 1 cache — refresh if missing, else use disk cache
        tier1 = load_tier1_cache()
        if not tier1.get("permits"):
            tier1 = refresh_tier1()
        tier1_permits = tier1.get("permits", {})

        # Build Tier 1 totals per bucket
        tier1_by_bucket: dict[str, dict] = {}
        for entry in tier1_permits.values():
            b = entry.get("bucket", "")
            row = tier1_by_bucket.setdefault(b, {"count": 0, "total": 0.0})
            row["count"] += 1
            row["total"] += entry.get("tier1_estimate_usd", 0)

        # Also sum Tier 3 (takeoff) values from generated addresses
        tier3_total = 0.0
        for addr_data in state.get("addresses", {}).values():
            slug = addr_data.get("slug")
            if slug and addr_data.get("status") == "generated":
                takeoff = _load_takeoff(slug)
                if takeoff:
                    tier3_total += sum(
                        t.get("pricing", {}).get("total", 0)
                        for t in takeoff.get("trades", [])
                    )

        pipeline_total = sum(r["total"] for r in tier1_by_bucket.values()) + tier3_total

        # Bucket cards with Tier 1 data merged
        bucket_cards = []
        for b in buckets_raw:
            name = b.get("bucket", "")
            raw = b.get("count_raw") or 0
            t1 = tier1_by_bucket.get(name, {"count": 0, "total": 0.0})
            bucket_cards.append({
                "name": name,
                "label": BUCKET_LABELS.get(name, name),
                "count_raw": raw,
                "count_clustered": b.get("count_clustered", 0),
                "tier1_count": t1["count"],
                "tier1_total": t1["total"],
                "total_initial_cost_usd": b.get("total_initial_cost_usd", 0),
            })

        def _fmt_value(v):
            if v >= 1e9:
                return f"${v/1e9:.1f}B"
            if v >= 1e6:
                return f"${v/1e6:.1f}M"
            if v >= 1e3:
                return f"${v/1e3:.0f}K"
            return f"${v:,.0f}"

        # RFP counts
        rfps_built = sum(
            1 for v in state.get("addresses", {}).values()
            if v.get("rfp_built_at")
        )
        rfps_sent = sum(
            1 for v in state.get("addresses", {}).values()
            if v.get("rfp_hook_status") == "sent"
        )

        metrics = [
            {"label": "Active Opportunities", "value": f"{total_permits:,}"},
            {"label": "Pipeline Value", "value": _fmt_value(pipeline_total)},
            {"label": "RFPs Built", "value": str(rfps_built)},
            {"label": "RFPs Sent", "value": str(rfps_sent)},
            {"label": "Proposals Sent", "value": str(sent_count)},
        ]
        return render_template(
            "dashboard.html",
            metrics=metrics,
            bucket_cards=bucket_cards,
            scan_date=scan.get("generated_at", ""),
            borough=scan.get("borough", ""),
            active_page="dashboard",
        )

    @app.route("/bucket/<name>")
    def bucket_view(name: str):
        scan = _latest_scan()
        bucket = next(
            (b for b in scan.get("buckets", []) if b.get("bucket") == name),
            None,
        )
        if bucket is None:
            abort(404)

        state = load_state()
        addrs = state.get("addresses", {})
        tier1 = load_tier1_cache().get("permits", {})

        permits = []
        neighborhoods = set()
        tier1_total = 0.0
        proposals_ready = 0
        for p in bucket.get("top_10", []):
            address = p.get("address", "")
            slug = _slugify_address(address)
            status = addrs.get(address, {}).get("status", "not_generated")
            neighborhood = p.get("borough") or p.get("neighborhood") or ""
            if neighborhood:
                neighborhoods.add(neighborhood)

            # Tier 3 (takeoff) value takes priority over Tier 1
            takeoff = _load_takeoff(slug)
            tier3_value = None
            tier3_confidence = None
            if takeoff:
                tier3_value = sum(
                    t.get("pricing", {}).get("total", 0)
                    for t in takeoff.get("trades", [])
                )
                # Use average confidence from trades
                confs = [t.get("confidence", "medium") for t in takeoff.get("trades", [])]
                tier3_confidence = max(set(confs), key=confs.count) if confs else "medium"
                proposals_ready += 1

            t1_entry = tier1.get(slug, {})
            t1_est = t1_entry.get("tier1_estimate_usd", 0)
            tier1_total += tier3_value if tier3_value else t1_est

            # RFP status
            addr_entry = addrs.get(address, {})
            rfp_status = "none"
            if addr_entry.get("rfp_hook_status") == "sent":
                resp_status = addr_entry.get("rfp_response_status")
                if resp_status == "interested":
                    rfp_status = "interested"
                elif resp_status == "not_interested":
                    rfp_status = "not_interested"
                else:
                    rfp_status = "hook_sent"
            elif addr_entry.get("rfp_built_at"):
                rfp_status = "rfp_ready"

            permits.append({
                "address": address,
                "year_built": p.get("year_built"),
                "job_type": p.get("job_type"),
                "bldg_area_sqft": p.get("bldg_area_sqft"),
                "initial_cost_usd": p.get("initial_cost_usd"),
                "neighborhood": neighborhood,
                "status": status,
                "slug": slug,
                "tier1_estimate": t1_est,
                "tier3_value": tier3_value,
                "tier3_confidence": tier3_confidence,
                "rfp_status": rfp_status,
            })

        avg_deal = tier1_total / len(permits) if permits else 0
        return render_template(
            "bucket.html",
            bucket=bucket,
            bucket_label=BUCKET_LABELS.get(name, name),
            permits=permits,
            tier1_total=tier1_total,
            proposals_ready=proposals_ready,
            avg_deal=avg_deal,
            neighborhoods=sorted(neighborhoods),
            active_page=f"bucket_{name}",
        )

    @app.route("/proposal/<slug>")
    def proposal_view(slug: str):
        takeoff = _load_takeoff(slug)
        has_pdf = _find_proposal_pdf(slug) is not None
        has_drip = _find_drip_schedule(slug) is not None

        # Status from pipeline_state
        state = load_state()
        addr_entry = None
        address_display = slug.replace("_", " ").title()
        for addr, entry in state.get("addresses", {}).items():
            if _slugify_address(addr) == slug:
                addr_entry = entry
                address_display = addr
                break

        status = (addr_entry or {}).get("status", "not_generated")
        contact_email = (addr_entry or {}).get("contact_email", "")

        grand_total = 0
        if takeoff:
            grand_total = sum(
                t.get("pricing", {}).get("total", 0) for t in takeoff.get("trades", [])
            )

        # Documents from dob_output/<slug>/
        doc_dir = DOB_OUTPUT_DIR / slug
        documents = []
        if doc_dir.exists():
            for f in sorted(doc_dir.iterdir()):
                if f.is_file():
                    documents.append({
                        "name": f.name,
                        "size": f.stat().st_size,
                        "ext": f.suffix.lower(),
                    })

        # Drip schedule
        drip_emails = []
        drip_data = {}
        drip_path = _find_drip_schedule(slug)
        if drip_path:
            with open(drip_path) as f:
                drip_data = json.load(f)
            drip_emails = _emails_from_drip(drip_data)

        # Bucket info for breadcrumb
        tier1 = load_tier1_cache().get("permits", {})
        t1_entry = tier1.get(slug, {})
        bucket_name = t1_entry.get("bucket", "")

        # RFP state
        rfp_html_path = REPO_ROOT / "rfps" / f"{slug}_rfp.html"
        has_rfp = rfp_html_path.exists()
        rfp_html_content = ""
        if has_rfp:
            rfp_html_content = rfp_html_path.read_text(encoding="utf-8")

        return render_template(
            "proposal.html",
            slug=slug,
            takeoff=takeoff,
            grand_total=grand_total,
            has_pdf=has_pdf,
            has_drip=has_drip,
            status=status,
            address=address_display,
            contact_email=contact_email,
            documents=documents,
            drip_emails=drip_emails,
            drip_data=drip_data,
            bucket_name=bucket_name,
            bucket_label=BUCKET_LABELS.get(bucket_name, bucket_name),
            has_rfp=has_rfp,
            rfp_html_content=rfp_html_content,
            active_page="",
        )

    @app.route("/proposal/<slug>/pdf")
    def proposal_pdf(slug: str):
        pdf = _find_proposal_pdf(slug)
        if pdf is None:
            abort(404)
        return send_file(
            str(pdf),
            mimetype="application/pdf",
            as_attachment=False,
            download_name=pdf.name,
        )

    @app.route("/outreach/<slug>")
    def outreach_view(slug: str):
        drip_path = _find_drip_schedule(slug)
        if drip_path is None:
            abort(404)
        with open(drip_path) as f:
            drip = json.load(f)
        emails = _emails_from_drip(drip)
        return render_template(
            "outreach.html",
            slug=slug,
            drip=drip,
            emails=emails,
        )

    @app.route("/generate", methods=["POST"])
    def generate():
        address = (request.form.get("address") or request.json.get("address") if request.is_json else request.form.get("address")) or ""
        address = address.strip()
        if not address:
            return jsonify({"error": "address required"}), 400
        set_address_state(address, status="queued", step="queued")
        thread = threading.Thread(
            target=_run_pipeline, args=(address,), daemon=True
        )
        thread.start()
        return jsonify({"ok": True, "address": address})

    @app.route("/generate/status")
    def generate_status():
        address = request.args.get("address", "").strip()
        state = load_state()
        if not address:
            return jsonify(state)
        return jsonify(state.get("addresses", {}).get(address, {"status": "unknown"}))

    @app.route("/generate/stream")
    def generate_stream():
        address = request.args.get("address", "").strip()

        @stream_with_context
        def gen():
            last = None
            for _ in range(600):  # up to ~10 min
                state = load_state()
                cur = state.get("addresses", {}).get(address, {})
                payload = json.dumps(cur)
                if payload != last:
                    yield f"data: {payload}\n\n"
                    last = payload
                if cur.get("status") in {"generated", "error"}:
                    break
                time.sleep(1)

        return Response(gen(), mimetype="text/event-stream")

    @app.route("/api/contact/<slug>", methods=["POST"])
    def save_contact_email(slug: str):
        """Save contact email to pipeline_state.json."""
        data = request.get_json(force=True)
        email = (data.get("email") or "").strip()
        state = load_state()
        for addr, entry in state.get("addresses", {}).items():
            if _slugify_address(addr) == slug:
                entry["contact_email"] = email
                state["addresses"][addr] = entry
                save_state(state)
                return jsonify({"ok": True})
        # Create entry if not found
        addr_display = slug.replace("_", " ").title()
        set_address_state(addr_display, contact_email=email, slug=slug)
        return jsonify({"ok": True})

    @app.route("/api/proposal/save/<slug>", methods=["POST"])
    def save_proposal_edits(slug: str):
        """Save edited proposal data back to takeoff.json."""
        data = request.get_json(force=True)
        takeoff_path = DOB_OUTPUT_DIR / slug / "takeoff.json"
        if not takeoff_path.exists():
            return jsonify({"error": "no takeoff"}), 404
        with open(takeoff_path) as f:
            takeoff = json.load(f)
        # Update trades from posted data
        takeoff["trades"] = data.get("trades", takeoff.get("trades", []))
        takeoff["overhead_pct"] = data.get("overhead_pct", 0.10)
        takeoff["profit_pct"] = data.get("profit_pct", 0.10)
        tmp = takeoff_path.with_suffix(".json.tmp")
        with open(tmp, "w") as f:
            json.dump(takeoff, f, indent=2)
        os.replace(tmp, takeoff_path)
        return jsonify({"ok": True})

    @app.route("/api/approve/<slug>", methods=["POST"])
    def approve_proposal(slug: str):
        """Set proposal status to approved."""
        state = load_state()
        for addr, entry in state.get("addresses", {}).items():
            if _slugify_address(addr) == slug:
                entry["status"] = "approved"
                state["addresses"][addr] = entry
                save_state(state)
                return jsonify({"ok": True})
        return jsonify({"error": "not found"}), 404

    @app.route("/api/export/<slug>")
    def export_excel(slug: str):
        """Export proposal to Excel using openpyxl."""
        takeoff = _load_takeoff(slug)
        if not takeoff:
            abort(404)
        try:
            from .excel_exporter import export_takeoff_to_excel
        except ImportError:
            return jsonify({"error": "openpyxl not installed"}), 500
        import tempfile
        out_path = Path(tempfile.mktemp(suffix=".xlsx"))
        export_takeoff_to_excel(takeoff, out_path)
        return send_file(
            str(out_path),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"{slug}_sanz_construction_proposal.xlsx",
        )

    @app.route("/generate/progress/<slug>")
    def generate_progress(slug: str):
        address = request.args.get("address", "").strip()
        return render_template(
            "progress.html",
            slug=slug,
            address=address,
            active_page="",
        )

    @app.route("/generate/status/<slug>")
    def generate_status_by_slug(slug: str):
        """Status endpoint by slug — scans pipeline_state for matching slug."""
        state = load_state()
        # Try matching by slug in address entries
        for addr, entry in state.get("addresses", {}).items():
            if _slugify_address(addr) == slug:
                return jsonify(entry)
        # Also check if passed as address query param
        address = request.args.get("address", "").strip()
        if address:
            return jsonify(state.get("addresses", {}).get(address, {"status": "unknown"}))
        return jsonify({"status": "unknown"})

    # ------------------------------------------------------------------
    # RFP routes (Sprint D1)
    # ------------------------------------------------------------------

    @app.route("/rfp/<slug>")
    def rfp_view(slug: str):
        """Full RFP view with inline HTML and send button."""
        rfp_html_path = REPO_ROOT / "rfps" / f"{slug}_rfp.html"
        rfp_exists = rfp_html_path.exists()
        rfp_html_content = ""
        if rfp_exists:
            rfp_html_content = rfp_html_path.read_text(encoding="utf-8")

        # RFP state
        import sys
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from drafted.rfp_state import get_rfp_state
        rfp_state = get_rfp_state(slug)

        address_display = slug.replace("_", " ").title()
        state = load_state()
        for addr, entry in state.get("addresses", {}).items():
            if _slugify_address(addr) == slug:
                address_display = addr
                break

        return render_template(
            "rfp.html",
            slug=slug,
            address=address_display,
            rfp_exists=rfp_exists,
            rfp_html_content=rfp_html_content,
            rfp_state=rfp_state,
            active_page="",
        )

    @app.route("/rfp/<slug>/pdf")
    def rfp_pdf(slug: str):
        pdf_path = REPO_ROOT / "rfps" / f"{slug}_rfp.pdf"
        if not pdf_path.exists():
            abort(404)
        return send_file(str(pdf_path), mimetype="application/pdf",
                         as_attachment=True, download_name=f"{slug}_rfp.pdf")

    @app.route("/rfp/build/<slug>", methods=["POST"])
    def rfp_build(slug: str):
        """Trigger firm scrape + RFP build for one address."""
        import sys
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from drafted.firm_scraper import scrape_firm
        from drafted.rfp_builder import build_rfp
        from drafted.rfp_state import update_rfp_state

        # Get applicant name from takeoff or state
        takeoff = _load_takeoff(slug)
        applicant = ""
        if takeoff:
            applicant = (takeoff.get("permit", {}) or {}).get("applicant_last_name") or ""
            if not applicant:
                applicant = (takeoff.get("resolved", {}) or {}).get("owner_name") or ""

        # Scrape firm
        firm_info = scrape_firm(applicant or slug.replace("_", " ").title())

        # Build RFP
        result = build_rfp(slug, firm_info)

        # Update state
        from datetime import datetime, timezone
        update_rfp_state(
            slug,
            firm_name=firm_info.get("firm_name"),
            firm_email=firm_info.get("email"),
            firm_logo_url=firm_info.get("logo_url"),
            firm_scrape_source=firm_info.get("source"),
            rfp_built_at=datetime.now(timezone.utc).isoformat(),
            rfp_pdf_path=result.get("pdf_path"),
            rfp_html_path=result.get("html_path"),
        )

        return jsonify({"ok": True, **result})

    @app.route("/rfp/build-batch", methods=["POST"])
    def rfp_build_batch():
        """Build RFPs for top 20 uncontacted addresses in a bucket."""
        import sys
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from drafted.rfp_state import get_rfp_state

        bucket_name = (request.get_json(force=True) or {}).get("bucket", "Abatement")
        scan = _latest_scan()
        bucket = next((b for b in scan.get("buckets", []) if b.get("bucket") == bucket_name), None)
        if not bucket:
            return jsonify({"error": "bucket not found"}), 404

        built = []
        for p in (bucket.get("top_10") or [])[:20]:
            address = p.get("address", "")
            slug = _slugify_address(address)
            rfp_st = get_rfp_state(slug)
            if rfp_st.get("rfp_built_at"):
                continue  # Already built
            # Build in foreground (could be threaded for perf)
            try:
                with app.test_request_context():
                    resp = rfp_build(slug)
                    built.append(slug)
            except Exception:
                pass

        return jsonify({"ok": True, "built": built, "count": len(built)})

    @app.route("/rfp/send-hook/<slug>", methods=["POST"])
    def rfp_send_hook(slug: str):
        """Send hook email for an address."""
        import sys
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from drafted.rfp_outreach import send_rfp_hook
        from drafted.rfp_state import get_rfp_state, update_rfp_state

        rfp_st = get_rfp_state(slug)
        pdf_path = rfp_st.get("rfp_pdf_path") or str(REPO_ROOT / "rfps" / f"{slug}_rfp.pdf")

        firm_info = {
            "firm_name": rfp_st.get("firm_name"),
            "email": rfp_st.get("firm_email"),
        }

        result = send_rfp_hook(slug, firm_info, pdf_path)

        update_rfp_state(
            slug,
            rfp_hook_sent_at=result.get("timestamp"),
            rfp_hook_status=result.get("status"),
        )

        return jsonify(result)

    @app.route("/healthz")
    def healthz():
        return {"ok": True}

    return app


def _emails_from_drip(drip: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten drip schedule into a list of 5 email rows."""
    emails: list[dict[str, Any]] = []
    initial = drip.get("initial_email") or {}
    if initial:
        emails.append(
            {
                "day": 0,
                "subject": initial.get("subject", ""),
                "body": initial.get("body", ""),
                "send_date": initial.get("send_date", "today"),
                "status": "sent" if initial.get("sent") else "scheduled",
            }
        )
    for f in drip.get("followups", []) or []:
        emails.append(
            {
                "day": f.get("day"),
                "subject": f.get("subject", ""),
                "body": f.get("body", ""),
                "send_date": f.get("send_date", f"+{f.get('day')}d"),
                "status": "sent" if f.get("sent") else "scheduled",
            }
        )
    return emails


def _run_pipeline(address: str) -> None:
    """Run the full pipeline for a single address via pipeline_runner.

    Chains: dob_puller → takeoff_engine → proposal_generator → outreach_engine.
    Updates pipeline_state.json at each step so the progress page can show
    live status.
    """
    import sys
    # Ensure repo root is on sys.path so the engine imports work
    repo_str = str(REPO_ROOT)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)
    # Must import here (not top-level) — the engine modules depend on being
    # importable from repo root, which may not be on PYTHONPATH at Flask boot.
    from permit_scanner.pipeline_runner import run_full_pipeline  # noqa: E402

    slug = _slugify(address)
    ranked = {"address": address, "score": 0}

    try:
        set_address_state(address, status="running", step="dob_puller", slug=slug)

        artifacts = run_full_pipeline(
            ranked,
            contractor="sanz_construction",
            trades=["abatement", "concrete", "demo"],
            use_playwright=False,
        )

        # Check for stage-level errors
        for key in ("dob_puller_error", "takeoff_engine_error", "proposal_error"):
            if key in artifacts:
                failed_step = key.replace("_error", "")
                set_address_state(
                    address,
                    status="error",
                    step=failed_step,
                    slug=slug,
                    error=str(artifacts[key]),
                )
                return

        # Verify takeoff was written
        takeoff_path = REPO_ROOT / "dob_output" / slug / "takeoff.json"
        if takeoff_path.exists():
            set_address_state(address, status="generated", step="complete", slug=slug)
        else:
            set_address_state(
                address,
                status="error",
                step="pipeline",
                slug=slug,
                error="Pipeline finished but no takeoff.json was written.",
            )
    except Exception as e:  # noqa: BLE001
        set_address_state(address, status="error", step="exception", slug=slug, error=str(e))


def _slugify(address: str) -> str:
    """Slugify address — must match portal's _slugify_address (inside create_app)."""
    s = (address or "").lower().strip()
    for ch in [",", ".", "'", '"']:
        s = s.replace(ch, "")
    return "_".join(s.split())


# Module-level app for `flask --app portal.app run` and WSGI servers.
app = create_app()
