# Railway Deployment Guide

This guide walks you through deploying OpenClaw Trade Assistant to Railway for 24/7 continuous operation.

## Prerequisites

Before deploying to Railway, you need:
- A Railway account (free tier available at [railway.app](https://railway.app))
- Your Gmail OAuth credentials already set up locally
- A GitHub account (recommended for easy deployment)

## Step 1: Generate Gmail Token Locally

Railway can't run the interactive OAuth flow, so you need to generate the token locally first.

### 1.1 Run the Gmail test locally

```bash
cd /Users/ianjaffrey/openclaw
python3 test_gmail_listener.py
```

This will open a browser window for Gmail OAuth authorization. Complete the authorization.

### 1.2 Verify token.json was created

```bash
ls -la token.json
```

You should see `token.json` in your project directory. This file contains your OAuth credentials.

**IMPORTANT:** Keep this file secure - it has access to your Gmail account!

## Step 2: Prepare credentials.json

Your `credentials.json` file (from Google Cloud Console) needs to be available to Railway.

### Option A: Environment Variable (Recommended)

Convert credentials.json to a single-line string:

```bash
cat credentials.json | jq -c '.'
```

Copy the output - you'll paste this into Railway as `GMAIL_CREDENTIALS_JSON`.

### Option B: Commit to private repo

If using a private GitHub repo, you can commit credentials.json:

```bash
git add credentials.json
git commit -m "Add Gmail credentials for Railway deployment"
```

**WARNING:** Never commit credentials to a public repo!

## Step 3: Prepare token.json

Convert token.json to a single-line string:

```bash
cat token.json | jq -c '.'
```

Copy the output - you'll paste this into Railway as `GMAIL_TOKEN_JSON`.

## Step 4: Push to GitHub (Recommended)

Railway works best with GitHub integration.

### 4.1 Create a new GitHub repository

Go to https://github.com/new and create a private repository called `openclaw`.

### 4.2 Push your code

```bash
git remote add origin https://github.com/YOUR_USERNAME/openclaw.git
git branch -M main
git push -u origin main
```

## Step 5: Deploy to Railway

### 5.1 Create Railway account

1. Go to [railway.app](https://railway.app)
2. Click "Login" and sign in with GitHub
3. Authorize Railway to access your GitHub account

### 5.2 Create new project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your `openclaw` repository
4. Railway will automatically detect the project and start building

### 5.3 Configure environment variables

Click on your deployed service, then go to "Variables" tab. Add these variables:

**Required variables:**
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
ANTHROPIC_API_KEY=your_anthropic_key
GMAIL_USER_EMAIL=your_gmail_address
```

**OAuth credentials (if using environment variables):**
```
GMAIL_CREDENTIALS_JSON={"installed":{"client_id":"...","project_id":"...",...}}
GMAIL_TOKEN_JSON={"token":"...","refresh_token":"...","token_uri":"...",...}
```

**Notes:**
- Paste the entire single-line JSON strings you created in Steps 2 and 3
- No quotes around the JSON strings in Railway's UI
- Click "Add" after each variable

## Step 6: Update gmail_listener.py for Railway

Railway needs to load credentials from environment variables instead of files.

Add this helper function to `gmail_listener.py`:

```python
import os
import json

def get_credentials_path():
    """Get credentials, from env var or file"""
    # Check if running on Railway (RAILWAY_ENVIRONMENT is set)
    if os.getenv('RAILWAY_ENVIRONMENT'):
        # Load from environment variable
        creds_json = os.getenv('GMAIL_CREDENTIALS_JSON')
        if creds_json:
            # Write to temporary file
            with open('/tmp/credentials.json', 'w') as f:
                json.dump(json.loads(creds_json), f)
            return '/tmp/credentials.json'

    # Default to local file
    return 'credentials.json'

def get_token_path():
    """Get token, from env var or file"""
    # Check if running on Railway
    if os.getenv('RAILWAY_ENVIRONMENT'):
        # Load from environment variable
        token_json = os.getenv('GMAIL_TOKEN_JSON')
        if token_json:
            # Write to temporary file
            with open('/tmp/token.json', 'w') as f:
                json.dump(json.loads(token_json), f)
            return '/tmp/token.json'

    # Default to local file
    return 'token.json'
```

Then update the `get_service()` function to use these helpers.

**Alternative:** Commit credentials.json and token.json to your private repo if you used Option B in Steps 2-3.

## Step 7: Configure the Procfile

Railway uses the `Procfile` to know how to run your app. It should contain:

```
worker: python3 main.py
```

This tells Railway to run `main.py` as a worker process (not a web server).

## Step 8: Deploy and Monitor

### 8.1 Trigger deployment

Railway auto-deploys when you push to GitHub:

```bash
git add .
git commit -m "Configure for Railway deployment"
git push origin main
```

Railway will automatically:
1. Detect the push
2. Build the project
3. Install dependencies from requirements.txt
4. Start the worker process

### 8.2 Monitor logs

1. Go to your Railway project
2. Click on your service
3. Click "Deployments" tab
4. Click on the latest deployment
5. View real-time logs

You should see:
```
🦞 OpenClaw Trade Assistant - Lead Processor
✓ Supabase connection successful
✓ Gmail service authenticated
Polling for new leads every 30 seconds...
```

### 8.3 Check for errors

Common issues:
- **Authentication failed:** Check GMAIL_CREDENTIALS_JSON and GMAIL_TOKEN_JSON
- **Database connection failed:** Check SUPABASE_URL and SUPABASE_KEY
- **Import errors:** Make sure requirements.txt is complete

## Step 9: Test the Deployment

### 9.1 Send a test email

Send a test lead email to your monitored Gmail address.

### 9.2 Check Railway logs

You should see:
```
✓ New lead detected: <subject>
✓ Lead parsed successfully
✓ Lead saved to database: <id>
✓ Reply generated (X words)
✓ Reply sent to <email>
```

### 9.3 Verify in Supabase

Check your Supabase dashboard - you should see the new lead in the `leads` table.

## Step 10: Keep It Running

Railway's free tier includes:
- 500 hours/month of runtime (enough for 24/7 operation)
- $5 of credit per month

Your app will run continuously without your laptop being on!

### Monitor usage

1. Go to Railway dashboard
2. Click "Usage" to see your monthly consumption
3. Upgrade to Hobby plan ($5/month) if you exceed free tier

## Troubleshooting

### OAuth token expires

If you see "Token has been expired or revoked" errors:

1. Run `python3 test_gmail_listener.py` locally to refresh the token
2. Convert new token.json to single-line JSON
3. Update `GMAIL_TOKEN_JSON` environment variable in Railway
4. Railway will auto-restart with new token

### Environment variables not loading

Make sure:
- Variable names are exact (case-sensitive)
- No extra quotes around values
- Click "Add" after each variable
- Redeploy after adding variables

### Credentials not found

If using environment variables, make sure:
- `GMAIL_CREDENTIALS_JSON` and `GMAIL_TOKEN_JSON` are set
- JSON is valid single-line format
- The helper functions in gmail_listener.py are implemented

### App crashes on startup

Check Railway logs for specific error messages:
- Missing dependencies → Add to requirements.txt
- Import errors → Check file paths
- Authentication errors → Verify credentials

## Security Best Practices

1. **Never commit credentials to public repos**
2. **Use environment variables for sensitive data**
3. **Keep your Railway project private**
4. **Rotate API keys periodically**
5. **Monitor Railway logs for suspicious activity**

## Updating the App

To deploy changes:

```bash
git add .
git commit -m "Description of changes"
git push origin main
```

Railway will automatically detect the push and redeploy.

## Cost Optimization

Railway free tier is usually sufficient, but if you need to optimize:

1. **Increase polling interval:** Change from 30 seconds to 60 seconds in main.py
2. **Add sleep during off-hours:** Skip polling between midnight-6am
3. **Use webhooks:** Switch from polling to Gmail push notifications (advanced)

## Next Steps

✅ Your app is now running 24/7 on Railway!

- Monitor logs daily for the first week
- Send test emails to verify operation
- Onboard your first real business with `python3 onboard_business.py`
- Start forwarding real leads!
