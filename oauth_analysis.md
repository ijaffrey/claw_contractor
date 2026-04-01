# OAuth and FastAPI Integration Analysis

## Current Codebase Structure

### Main.py Analysis
- **Core System**: Lead Management System with email processing workflow
- **Pattern**: Uses absolute imports for modules (gmail_listener, lead_parser, etc.)
- **Architecture**: LeadManagementSystem class handles workflow orchestration
- **OAuth Evidence**: Lines 379 and 435 show Flask-style routes for Google OAuth:
  - `@app.route('/auth/google')` - OAuth initiation endpoint
  - `@app.route('/auth/google/callback')` - OAuth callback handler
- **Integration Point**: Conversation manager handles email reply routing
- **Dry Run Support**: System includes testing mode without side effects

### FastAPI Setup
- **Location**: patrick_web/app.py contains separate FastAPI application
- **Current State**: Basic FastAPI app with CORS middleware
- **Endpoints**: 
  - `/` - Landing page (HTML response)
  - `/api/health` - Health check endpoint
- **Missing**: No OAuth integration in FastAPI app yet
- **Static Files**: Configured to serve static files from /static
- **Server**: Uses uvicorn for ASGI serving

### Database Configuration
- **Pattern**: SQLAlchemy with declarative base models
- **Database**: Uses DATABASE_URL environment variable (defaults to SQLite)
- **Models**: Lead, NotificationLog models with enums for status tracking
- **Missing Supabase**: Current database.py uses SQLAlchemy, NOT Supabase client
- **OAuth Storage**: No user/session tables for OAuth token storage

### Configuration Management
- **File**: config.py provides environment-based configuration
- **Pattern**: Uses python-dotenv for .env file loading
- **Email**: SMTP configuration present for email functionality
- **Security**: Basic Flask security settings (CSRF, session cookies)
- **Missing**: No OAuth provider configuration (Google client ID/secret)

### Current Dependencies (requirements.txt)
- **Google APIs**: google-auth, google-auth-oauthlib, google-api-python-client
- **Database**: supabase==2.28.2 (but not used in database.py)
- **AI**: anthropic==0.84.0 for Claude integration
- **Utils**: python-dotenv, python-dateutil
- **Missing FastAPI**: No FastAPI listed in requirements.txt
- **Missing OAuth**: No FastAPI-specific OAuth dependencies

## Missing Dependencies for OAuth Integration

### Required FastAPI Dependencies
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6  # Form data handling
```

### Required OAuth Dependencies
```
python-jose[cryptography]>=3.3.0  # JWT token handling
passlib[bcrypt]>=1.7.4            # Password hashing
authlib>=1.2.1                    # OAuth provider integration
fastapi-users[sqlalchemy]>=12.1.0 # FastAPI authentication framework
```

### Database Migration Dependencies
```
alembic>=1.12.0                   # Database migrations
sqlalchemy[asyncio]>=2.0.0        # Async SQLAlchemy support
```

## Integration Requirements

### 1. Migrate from SQLAlchemy to Supabase
- Current database.py needs replacement with Supabase client
- OAuth requires user/session tables in Supabase
- Need environment variables: SUPABASE_URL, SUPABASE_ANON_KEY

### 2. FastAPI OAuth Setup
- Add FastAPI to requirements.txt
- Configure OAuth providers in FastAPI app
- Add user authentication endpoints
- Integrate with existing lead processing workflow

### 3. Environment Variables Needed
```
# OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback

# Supabase Configuration  
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Development Environment Status
- **FastAPI**: Partially implemented in patrick_web/app.py
- **OAuth**: Google OAuth routes exist in main.py but not integrated with FastAPI
- **Database**: SQLAlchemy setup exists but Supabase client needed
- **Dependencies**: Core Google Auth libraries present, FastAPI OAuth libraries missing
- **Configuration**: Basic config.py exists, OAuth environment variables missing

## Next Steps Required
1. Add missing FastAPI and OAuth dependencies to requirements.txt
2. Replace SQLAlchemy database.py with Supabase client implementation
3. Create user authentication tables in Supabase
4. Migrate OAuth routes from main.py Flask pattern to FastAPI in patrick_web/app.py
5. Configure OAuth environment variables
6. Test OAuth flow with existing lead management system