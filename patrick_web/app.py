from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import os
from pathlib import Path

# Create FastAPI app
app = FastAPI(title="Patrick Web Interface", version="1.0.0")

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Landing page route
@app.get("/")
async def landing_page():
    """Serve the ContractorAI landing page"""
    with open("landing/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi.templating import Jinja2Templates
from fastapi import Request

# Setup template rendering
templates = Jinja2Templates(directory="patrick_web/templates")

@app.get("/campaigns/leads")
async def campaigns_leads(request: Request):
    """Campaign leads management page"""
    # Mock data for leads table
    leads_data = [
        {
            "id": 1,
            "name": "John Smith Construction",
            "trade": "General Contractor",
            "borough": "Manhattan",
            "enrichment_score": 85,
            "outreach_status": "Not Contacted",
            "phone": "(555) 123-4567",
            "email": "john@smithconstruction.com",
            "permit_count": 12
        },
        {
            "id": 2,
            "name": "Brooklyn Builders LLC",
            "trade": "Electrical",
            "borough": "Brooklyn",
            "enrichment_score": 45,
            "outreach_status": "Contacted",
            "phone": "(555) 987-6543",
            "email": "info@brooklynbuilders.com",
            "permit_count": 8
        },
        {
            "id": 3,
            "name": "Queens Plumbing Co",
            "trade": "Plumbing",
            "borough": "Queens",
            "enrichment_score": 15,
            "outreach_status": "Proposal Sent",
            "phone": "(555) 456-7890",
            "email": "contact@queensplumbing.com",
            "permit_count": 3
        }
    ]
    return templates.TemplateResponse("campaigns/leads.html", {
        "request": request,
        "leads": leads_data,
        "title": "Campaign Leads"
    })

@app.get("/campaigns/leads")
async def campaigns_leads(request: Request):
    """Campaign leads page with contact table and filtering"""
    # Mock data for leads table
    leads_data = [
        {
            "id": 1,
            "name": "John Smith Construction",
            "trade": "General Contractor",
            "borough": "Manhattan",
            "enrichment_score": 85,
            "outreach_status": "Not Contacted",
            "phone": "(555) 123-4567",
            "email": "john@smithconstruction.com",
            "permit_count": 12
        },
        {
            "id": 2,
            "name": "Brooklyn Builders LLC",
            "trade": "Electrical",
            "borough": "Brooklyn",
            "enrichment_score": 45,
            "outreach_status": "Contacted",
            "phone": "(555) 987-6543",
            "email": "info@brooklynbuilders.com",
            "permit_count": 8
        },
        {
            "id": 3,
            "name": "Queens Plumbing Co",
            "trade": "Plumbing",
            "borough": "Queens",
            "enrichment_score": 15,
            "outreach_status": "Proposal Sent",
            "phone": "(555) 456-7890",
            "email": "contact@queensplumbing.com",
            "permit_count": 3
        }
    ]
    return templates.TemplateResponse("campaigns/leads.html", {
        "request": request,
        "leads": leads_data,
        "title": "Campaign Leads"
    })