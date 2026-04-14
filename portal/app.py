import os
import sys
import json
import logging
from datetime import datetime

from flask import Flask, jsonify, request, render_template, abort

# Ensure repo root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__, template_folder="templates")
logger = logging.getLogger(__name__)

# ── DB helpers (lazy, tolerates missing Supabase creds) ──────────────────────

def _get_db():
    """Return SQLAlchemy session using DATABASE_URL or sqlite fallback."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    db_url = os.getenv("DATABASE_URL", "sqlite:///leads.db")
    if db_url.startswith("sqlite"):
        engine = create_engine(db_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    else:
        engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session(), engine


# ── Health ─────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"})


# ── Campaign dashboard pages ───────────────────────────────────────────────

@app.route("/campaigns")
def campaigns_page():
    return render_template("campaign_dashboard.html")


@app.route("/campaigns/leads")
def campaign_leads_page():
    return render_template("campaign_dashboard.html")


# ── API: Leads with enrichment data ────────────────────────────────────────

@app.route("/api/campaigns/leads", methods=["GET"])
def api_list_leads():
    """Return leads with enrichment columns."""
    try:
        from sqlalchemy import text
        db, engine = _get_db()
        result = db.execute(text("""
            SELECT id, name, email, phone, company, source, status,
                   notes, score,
                   enriched_email, enriched_phone, website,
                   email_source, phone_source,
                   enrichment_status, enrichment_score, enriched_at,
                   campaign_tags, outreach_status, last_contacted_at,
                   created_at, updated_at
            FROM leads
            WHERE is_active = 1
            ORDER BY enrichment_score DESC, created_at DESC
            LIMIT 500
        """))
        cols = result.keys()
        leads = [dict(zip(cols, row)) for row in result.fetchall()]
        db.close()
        return jsonify({"leads": leads, "total": len(leads)})
    except Exception as e:
        logger.exception("api_list_leads failed")
        return jsonify({"leads": [], "total": 0, "error": str(e)}), 200


@app.route("/api/campaigns/leads/<int:lead_id>", methods=["PATCH"])
def api_update_lead(lead_id):
    """Patch enrichment / outreach fields on a lead."""
    data = request.get_json() or {}
    allowed = {
        "outreach_status", "last_contacted_at", "campaign_tags",
        "notes", "enriched_email", "enriched_phone", "website",
        "email_source", "phone_source", "enrichment_status",
        "enrichment_score", "enriched_at",
    }
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    try:
        from sqlalchemy import text
        db, _ = _get_db()
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["lead_id"] = lead_id
        db.execute(text(f"UPDATE leads SET {set_clause} WHERE id = :lead_id"), updates)
        db.commit()
        db.close()
        return jsonify({"ok": True, "lead_id": lead_id})
    except Exception as e:
        logger.exception("api_update_lead failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/campaigns/leads/<int:lead_id>/enrich", methods=["POST"])
def api_enrich_lead(lead_id):
    """Run enrichment waterfall on a single lead."""
    try:
        from sqlalchemy import text
        from drafted.enrichment_engine import enrich_lead

        db, _ = _get_db()
        row = db.execute(text("SELECT * FROM leads WHERE id = :id"), {"id": lead_id}).fetchone()
        if not row:
            return jsonify({"error": "Lead not found"}), 404

        lead_dict = dict(zip(row.keys(), row))
        result = enrich_lead(lead_dict)

        # Persist enrichment result
        db.execute(text("""
            UPDATE leads SET
                enriched_email      = :email,
                enriched_phone      = :phone,
                website             = :website,
                email_source        = :email_source,
                phone_source        = :phone_source,
                enrichment_status   = :enrichment_status,
                enrichment_score    = :enrichment_score,
                enriched_at         = :enriched_at
            WHERE id = :lead_id
        """), {**result, "lead_id": lead_id})
        db.commit()
        db.close()
        return jsonify({"ok": True, "lead_id": lead_id, "result": result})
    except Exception as e:
        logger.exception("api_enrich_lead failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/campaigns/leads/bulk-enrich", methods=["POST"])
def api_bulk_enrich():
    """Bulk enrich a list of leads."""
    data = request.get_json() or {}
    lead_ids = data.get("lead_ids", [])
    if not lead_ids:
        return jsonify({"error": "lead_ids required"}), 400

    try:
        from sqlalchemy import text
        from drafted.enrichment_engine import enrich_lead

        db, _ = _get_db()
        enriched = 0
        for lead_id in lead_ids:
            row = db.execute(text("SELECT * FROM leads WHERE id = :id"), {"id": lead_id}).fetchone()
            if not row:
                continue
            lead_dict = dict(zip(row.keys(), row))
            result = enrich_lead(lead_dict)
            db.execute(text("""
                UPDATE leads SET
                    enriched_email    = :email,
                    enriched_phone    = :phone,
                    website           = :website,
                    email_source      = :email_source,
                    phone_source      = :phone_source,
                    enrichment_status = :enrichment_status,
                    enrichment_score  = :enrichment_score,
                    enriched_at       = :enriched_at
                WHERE id = :lead_id
            """), {**result, "lead_id": lead_id})
            enriched += 1

        db.commit()
        db.close()
        return jsonify({"ok": True, "enriched": enriched})
    except Exception as e:
        logger.exception("api_bulk_enrich failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/campaigns/leads/<int:lead_id>/proposal", methods=["POST"])
def api_generate_proposal(lead_id):
    """Generate outreach proposal for a lead."""
    data = request.get_json() or {}
    brand = data.get("brand", "skipp")

    try:
        from sqlalchemy import text
        from drafted.proposal_generator import generate_proposal

        db, _ = _get_db()
        row = db.execute(text("SELECT * FROM leads WHERE id = :id"), {"id": lead_id}).fetchone()
        if not row:
            return jsonify({"error": "Lead not found"}), 404

        lead_dict = dict(zip(row.keys(), row))
        db.close()

        result = generate_proposal(lead_dict, brand=brand)
        return jsonify({"ok": True, "lead_id": lead_id, **result})
    except Exception as e:
        logger.exception("api_generate_proposal failed")
        return jsonify({"error": str(e)}), 500


# ── API: Campaigns CRUD ────────────────────────────────────────────────────

@app.route("/api/campaigns", methods=["GET"])
def api_list_campaigns():
    try:
        from sqlalchemy import text
        db, _ = _get_db()
        rows = db.execute(text("""
            SELECT c.*,
                   COUNT(cl.id) AS lead_count
            FROM campaigns c
            LEFT JOIN campaign_leads cl ON cl.campaign_id = c.id
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """)).fetchall()
        cols_raw = db.execute(text("SELECT * FROM campaigns LIMIT 0")).keys()
        campaigns = []
        for row in rows:
            d = dict(zip(list(cols_raw) + ["lead_count"], list(row)))
            campaigns.append(d)
        db.close()
        return jsonify({"campaigns": campaigns})
    except Exception as e:
        logger.exception("api_list_campaigns failed")
        return jsonify({"campaigns": [], "error": str(e)}), 200


@app.route("/api/campaigns", methods=["POST"])
def api_create_campaign():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    try:
        from sqlalchemy import text
        db, _ = _get_db()
        now = datetime.utcnow().isoformat()
        db.execute(text("""
            INSERT INTO campaigns (name, description, brand, status, target_trade, target_borough, created_at, updated_at)
            VALUES (:name, :description, :brand, :status, :target_trade, :target_borough, :created_at, :updated_at)
        """), {
            "name": name,
            "description": data.get("description", ""),
            "brand": data.get("brand", "skipp"),
            "status": data.get("status", "draft"),
            "target_trade": data.get("target_trade", ""),
            "target_borough": data.get("target_borough", ""),
            "created_at": now,
            "updated_at": now,
        })
        db.commit()
        row = db.execute(text("SELECT * FROM campaigns ORDER BY id DESC LIMIT 1")).fetchone()
        cols = db.execute(text("SELECT * FROM campaigns LIMIT 0")).keys()
        campaign = dict(zip(cols, row))
        db.close()
        return jsonify({"ok": True, "campaign": campaign}), 201
    except Exception as e:
        logger.exception("api_create_campaign failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/campaigns/<int:campaign_id>", methods=["GET"])
def api_get_campaign(campaign_id):
    try:
        from sqlalchemy import text
        db, _ = _get_db()
        row = db.execute(text("SELECT * FROM campaigns WHERE id = :id"), {"id": campaign_id}).fetchone()
        if not row:
            return jsonify({"error": "Campaign not found"}), 404
        cols = db.execute(text("SELECT * FROM campaigns LIMIT 0")).keys()
        campaign = dict(zip(cols, row))
        db.close()
        return jsonify({"campaign": campaign})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/campaigns/<int:campaign_id>", methods=["PATCH"])
def api_update_campaign(campaign_id):
    data = request.get_json() or {}
    allowed = {"name", "description", "brand", "status", "target_trade", "target_borough", "launched_at"}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return jsonify({"error": "No valid fields"}), 400

    updates["updated_at"] = datetime.utcnow().isoformat()
    updates["campaign_id"] = campaign_id

    try:
        from sqlalchemy import text
        db, _ = _get_db()
        set_clause = ", ".join(f"{k} = :{k}" for k in updates if k != "campaign_id")
        db.execute(text(f"UPDATE campaigns SET {set_clause} WHERE id = :campaign_id"), updates)
        db.commit()
        db.close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/campaigns/<int:campaign_id>", methods=["DELETE"])
def api_delete_campaign(campaign_id):
    try:
        from sqlalchemy import text
        db, _ = _get_db()
        db.execute(text("DELETE FROM campaigns WHERE id = :id"), {"id": campaign_id})
        db.commit()
        db.close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/campaigns/<int:campaign_id>/leads", methods=["GET"])
def api_get_campaign_leads(campaign_id):
    """Get leads assigned to a campaign."""
    try:
        from sqlalchemy import text
        db, _ = _get_db()
        result = db.execute(text("""
            SELECT l.*, cl.outreach_status AS cl_outreach, cl.added_at, cl.sent_at, cl.replied_at
            FROM leads l
            JOIN campaign_leads cl ON cl.lead_id = l.id
            WHERE cl.campaign_id = :cid
            ORDER BY l.enrichment_score DESC
        """), {"cid": campaign_id})
        cols = list(result.keys())
        rows = result.fetchall()
        if not rows:
            return jsonify({"leads": []})
        leads = [dict(zip(cols, row)) for row in rows]
        db.close()
        return jsonify({"leads": leads})
    except Exception as e:
        return jsonify({"leads": [], "error": str(e)}), 200


@app.route("/api/campaigns/<int:campaign_id>/leads", methods=["POST"])
def api_assign_leads(campaign_id):
    """Assign lead_ids to a campaign."""
    data = request.get_json() or {}
    lead_ids = data.get("lead_ids", [])
    if not lead_ids:
        return jsonify({"error": "lead_ids required"}), 400

    try:
        from sqlalchemy import text
        db, _ = _get_db()
        now = datetime.utcnow().isoformat()
        added = 0
        for lid in lead_ids:
            try:
                db.execute(text("""
                    INSERT OR IGNORE INTO campaign_leads (campaign_id, lead_id, added_at, outreach_status)
                    VALUES (:cid, :lid, :now, 'pending')
                """), {"cid": campaign_id, "lid": lid, "now": now})
                added += 1
            except Exception:
                pass
        db.commit()
        db.close()
        return jsonify({"ok": True, "added": added})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/campaigns/assign-leads", methods=["POST"])
def api_assign_leads_by_name():
    """Create or find campaign by name and assign leads."""
    data = request.get_json() or {}
    campaign_name = data.get("campaign_name", "").strip()
    lead_ids = data.get("lead_ids", [])

    if not campaign_name or not lead_ids:
        return jsonify({"error": "campaign_name and lead_ids required"}), 400

    try:
        from sqlalchemy import text
        db, _ = _get_db()
        row = db.execute(text("SELECT id FROM campaigns WHERE name = :name"), {"name": campaign_name}).fetchone()
        if row:
            campaign_id = row[0]
        else:
            now = datetime.utcnow().isoformat()
            db.execute(text("""
                INSERT INTO campaigns (name, brand, status, created_at, updated_at)
                VALUES (:name, 'skipp', 'draft', :now, :now)
            """), {"name": campaign_name, "now": now})
            db.commit()
            campaign_id = db.execute(text("SELECT id FROM campaigns ORDER BY id DESC LIMIT 1")).fetchone()[0]

        now = datetime.utcnow().isoformat()
        added = 0
        for lid in lead_ids:
            try:
                db.execute(text("""
                    INSERT OR IGNORE INTO campaign_leads (campaign_id, lead_id, added_at, outreach_status)
                    VALUES (:cid, :lid, :now, 'pending')
                """), {"cid": campaign_id, "lid": lid, "now": now})
                added += 1
            except Exception:
                pass
        db.commit()
        db.close()
        return jsonify({"ok": True, "campaign_id": campaign_id, "added": added})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/campaigns/<int:campaign_id>/stats", methods=["GET"])
def api_campaign_stats(campaign_id):
    """Return engagement stats for a campaign."""
    try:
        from sqlalchemy import text
        db, _ = _get_db()
        stats = db.execute(text("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN outreach_status = 'pending' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN outreach_status = 'sent' THEN 1 ELSE 0 END) AS sent,
                SUM(CASE WHEN outreach_status = 'replied' THEN 1 ELSE 0 END) AS replied,
                SUM(CASE WHEN outreach_status = 'converted' THEN 1 ELSE 0 END) AS converted,
                SUM(CASE WHEN sent_at IS NOT NULL THEN 1 ELSE 0 END) AS delivered
            FROM campaign_leads
            WHERE campaign_id = :cid
        """), {"cid": campaign_id}).fetchone()
        db.close()
        return jsonify({
            "campaign_id": campaign_id,
            "total": stats[0], "pending": stats[1], "sent": stats[2],
            "replied": stats[3], "converted": stats[4], "delivered": stats[5],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Bucket (permit list per trade) ────────────────────────────────────────

@app.route("/bucket/<trade>")
def bucket_page(trade):
    return render_template("bucket.html", trade=trade)


@app.route("/api/bucket/<trade>/leads", methods=["GET"])
def api_bucket_leads(trade):
    """Return permit leads for a given trade, with all enrichment columns."""
    try:
        from sqlalchemy import text
        db, _ = _get_db()
        all_trades = trade.lower() == "all"
        trade_filter = f"%{trade.lower()}%"
        result = db.execute(text("""
            SELECT id, name, email, phone, company, source, status, notes, score,
                   enriched_email, enriched_phone, website,
                   email_source, phone_source,
                   enrichment_status, enrichment_score, enriched_at,
                   campaign_tags, outreach_status, last_contacted_at,
                   created_at, updated_at
            FROM leads
            WHERE is_active = 1
              AND (
                :all_trades = 1
                OR LOWER(COALESCE(campaign_tags,'')) LIKE :trade
                OR LOWER(COALESCE(source,'')) LIKE :trade
              )
            ORDER BY created_at DESC
            LIMIT 500
        """), {"trade": trade_filter, "all_trades": 1 if all_trades else 0})
        cols = list(result.keys())
        rows = result.fetchall()
        leads = [dict(zip(cols, row)) for row in rows]
        db.close()
        return jsonify({"leads": leads, "total": len(leads), "trade": trade})
    except Exception as e:
        logger.exception("api_bucket_leads failed")
        return jsonify({"leads": [], "total": 0, "error": str(e)}), 200


@app.route("/api/leads/<int:lead_id>", methods=["GET"])
def api_get_lead_bucket(lead_id):
    """Return a single lead with all enrichment contact fields for the expand panel."""
    try:
        from sqlalchemy import text
        db, _ = _get_db()
        row = db.execute(text("""
            SELECT id, name, email, phone, company, source, status, notes, score,
                   enriched_email, enriched_phone, website,
                   email_source, phone_source,
                   enrichment_status, enrichment_score, enriched_at,
                   campaign_tags, outreach_status, last_contacted_at,
                   created_at, updated_at
            FROM leads WHERE id = :id
        """), {"id": lead_id}).fetchone()
        if not row:
            return jsonify({"error": "Lead not found"}), 404
        cols = list(row.keys())
        lead = dict(zip(cols, row))
        db.close()
        return jsonify({"lead": lead})
    except Exception as e:
        logger.exception("api_get_lead_bucket failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/leads/<int:lead_id>/enrich", methods=["POST"])
def api_enrich_lead_bucket(lead_id):
    """Alias for enriching a single lead — used by /bucket/<trade> UI."""
    return api_enrich_lead(lead_id)


@app.route("/api/leads/bulk-enrich", methods=["POST"])
def api_bulk_enrich_bucket():
    """Alias for bulk enrichment — used by /bucket/<trade> UI."""
    return api_bulk_enrich()


@app.route("/api/leads/credit-estimate", methods=["POST"])
def api_credit_estimate():
    """Return estimated API credit cost before running bulk enrichment.

    Body: {"lead_ids": [...]}
    Returns: {"lead_count": N, "credits_per_lead": 3, "total_credits": N*3,
              "already_enriched": M, "net_leads": N-M}
    """
    data = request.get_json() or {}
    lead_ids = data.get("lead_ids", [])
    if not lead_ids:
        return jsonify({"error": "lead_ids required"}), 400

    try:
        from sqlalchemy import text
        db, _ = _get_db()
        placeholders = ",".join(str(int(i)) for i in lead_ids if str(i).lstrip("-").isdigit())
        if not placeholders:
            return jsonify({"error": "invalid lead_ids"}), 400

        rows = db.execute(text(f"""
            SELECT id, enrichment_status FROM leads
            WHERE id IN ({placeholders})
        """)).fetchall()
        db.close()

        already = sum(1 for r in rows if r[1] == "complete")
        net = len(rows) - already
        credits_per_lead = 3
        return jsonify({
            "lead_count":      len(rows),
            "already_enriched": already,
            "net_leads":       net,
            "credits_per_lead": credits_per_lead,
            "total_credits":   net * credits_per_lead,
        })
    except Exception as e:
        logger.exception("api_credit_estimate failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/leads/<int:lead_id>", methods=["PATCH"])
def api_update_lead_bucket(lead_id):
    """Alias for lead patch — used by /bucket/<trade> UI."""
    return api_update_lead(lead_id)


@app.route("/api/leads/<int:lead_id>/proposal", methods=["POST"])
def api_proposal_bucket(lead_id):
    """Alias for proposal generation — used by /bucket/<trade> UI."""
    return api_generate_proposal(lead_id)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
