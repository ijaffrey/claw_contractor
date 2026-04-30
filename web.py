"""
ContractorAI Onboarding Web App
Flask app with landing page, Gmail OAuth, business profile form, and confirmation.
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, redirect, request, session, render_template, url_for
from google_auth_oauthlib.flow import Flow

import database as db

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates/web")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

# Google OAuth config
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
RAILWAY_DOMAIN = "worker-production-ed72.up.railway.app"
BASE_URL = os.getenv("BASE_URL", f"https://{RAILWAY_DOMAIN}")
GOOGLE_REDIRECT_URI = f"{BASE_URL}/callback"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

# Allow HTTP for local dev only
if os.getenv("FLASK_ENV") == "development":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


def get_oauth_flow():
    """Create Google OAuth flow from environment variables."""
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [GOOGLE_REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    return flow


# --- Routes ---


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/auth/gmail")
def auth_gmail():
    """Start Gmail OAuth flow."""
    flow = get_oauth_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    session["oauth_state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    """Handle Google OAuth callback, then redirect to onboarding form."""
    flow = get_oauth_flow()
    flow.fetch_token(authorization_response=request.url.replace("http://", "https://"))

    credentials = flow.credentials
    session["google_credentials"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes or []),
    }

    # Fetch user email from Google
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials(**session["google_credentials"])
    service = build("oauth2", "v2", credentials=creds)
    user_info = service.userinfo().get().execute()
    session["gmail_email"] = user_info.get("email", "")

    return redirect(url_for("onboard"))


@app.route("/onboard", methods=["GET", "POST"])
def onboard():
    """Business profile onboarding form."""
    if "google_credentials" not in session:
        return redirect(url_for("landing"))

    if request.method == "POST":
        business_data = {
            "name": request.form.get("business_name", "").strip(),
            "trade_type": request.form.get("trade_type", "").strip().lower(),
            "owner_name": request.form.get("owner_name", "").strip() or None,
            "email": session.get("gmail_email", request.form.get("email", "").strip()),
            "phone": request.form.get("phone", "").strip() or None,
            "service_area": request.form.get("service_area", "").strip() or None,
            "brand_voice": request.form.get("brand_voice", "").strip(),
        }

        # Store credentials alongside business profile
        business_data["google_credentials"] = json.dumps(session["google_credentials"])

        try:
            saved = db.insert_business(business_data)
            if saved:
                session["business_name"] = business_data["name"]
                session["business_email"] = business_data["email"]
                return redirect(url_for("live"))
        except Exception as e:
            logger.error(f"Failed to save business: {e}")
            return render_template(
                "onboard.html",
                error="Something went wrong saving your profile. Please try again.",
                gmail_email=session.get("gmail_email", ""),
            )

    return render_template("onboard.html", gmail_email=session.get("gmail_email", ""))


@app.route("/live")
def live():
    """You're live confirmation page."""
    if "business_name" not in session:
        return redirect(url_for("landing"))

    return render_template(
        "live.html",
        business_name=session.get("business_name", ""),
        business_email=session.get("business_email", ""),
    )


# --- Health check for Railway ---


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    debug = os.getenv("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
