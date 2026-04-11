"""ContractorAI portal — Flask web UI for Nauman's bid pipeline.

Mobile-first. Reads pipeline artifacts directly from disk (scan_results/,
dob_output/, proposals/) so it can run alongside the existing CLI pipeline.
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
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
        buckets = scan.get("buckets", [])
        total_permits = scan.get("permits_fetched", 0)
        total_clustered = sum(b.get("count_clustered", 0) for b in buckets)
        total_value = sum(b.get("total_initial_cost_usd", 0) for b in buckets)
        active_buckets = sum(1 for b in buckets if b.get("count_raw", 0) > 0)
        state = load_state()
        generated_count = sum(
            1
            for v in state.get("addresses", {}).values()
            if v.get("status") == "generated"
        )

        metrics = [
            {"label": "Permits Scanned", "value": f"{total_permits:,}"},
            {"label": "Clustered Leads", "value": f"{total_clustered:,}"},
            {"label": "Active Buckets", "value": str(active_buckets)},
            {
                "label": "Pipeline Value",
                "value": f"${total_value/1e9:.1f}B" if total_value else "$0",
            },
            {"label": "Proposals Generated", "value": str(generated_count)},
        ]
        return render_template(
            "dashboard.html",
            metrics=metrics,
            buckets=buckets,
            scan_date=scan.get("generated_at", ""),
            borough=scan.get("borough", ""),
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
        permits = []
        for p in bucket.get("top_10", []):
            address = p.get("address", "")
            slug = _slugify_address(address)
            status = addrs.get(address, {}).get("status", "new")
            permits.append(
                {
                    "address": address,
                    "year_built": p.get("year_built"),
                    "job_type": p.get("job_type"),
                    "bldg_area_sqft": p.get("bldg_area_sqft"),
                    "initial_cost_usd": p.get("initial_cost_usd"),
                    "status": status,
                    "slug": slug,
                }
            )
        return render_template(
            "bucket.html",
            bucket=bucket,
            permits=permits,
        )

    @app.route("/proposal/<slug>")
    def proposal_view(slug: str):
        takeoff = _load_takeoff(slug)
        if takeoff is None:
            abort(404)

        grand_total = sum(
            t.get("pricing", {}).get("total", 0) for t in takeoff.get("trades", [])
        )
        has_pdf = _find_proposal_pdf(slug) is not None
        has_drip = _find_drip_schedule(slug) is not None
        return render_template(
            "proposal.html",
            slug=slug,
            takeoff=takeoff,
            grand_total=grand_total,
            has_pdf=has_pdf,
            has_drip=has_drip,
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
    """Invoke the existing CLI pipeline as a subprocess and update state."""
    try:
        set_address_state(address, status="running", step="dob_puller")
        proc = subprocess.run(
            ["python3", "main.py", "--address", address],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=600,
        )
        if proc.returncode != 0:
            set_address_state(
                address,
                status="error",
                step="pipeline",
                error=proc.stderr[-800:],
            )
            return
        set_address_state(address, status="generated", step="complete")
    except Exception as e:  # noqa: BLE001
        set_address_state(address, status="error", step="exception", error=str(e))


# Module-level app for `flask --app portal.app run` and WSGI servers.
app = create_app()
