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

## Step 2: Prepare token.json

Convert token.json to a single-line string:

```bash
cat token.json | jq -c '.'
```

Copy the output - you'll paste this into Railway as `GMAIL_TOKEN_JSON`.

**Note:** The token JSON contains everything needed (token, refresh_token, client_id, client_secret, scopes). You do NOT need to set GMAIL_CREDENTIALS_JSON separately!

## Step 3: Push to GitHub (Recommended)

Railway works best with GitHub integration.

### 3.1 Create a new GitHub repository

Go to https://github.com/new and create a private repository called `openclaw`.

### 3.2 Push your code

```bash
git remote add origin https://github.com/YOUR_USERNAME/openclaw.git
git branch -M main
git push -u origin main
```

## Step 4: Deploy to Railway

### 4.1 Create Railway account

1. Go to [railway.app](https://railway.app)
2. Click "Login" and sign in with GitHub
3. Authorize Railway to access your GitHub account

### 4.2 Create new project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your `openclaw` repository
4. Railway will automatically detect the project and start building

### 4.3 Configure environment variables

Click on your deployed service, then go to "Variables" tab. Add these variables:

**Required variables:**
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
ANTHROPIC_API_KEY=your_anthropic_key
GMAIL_USER_EMAIL=your_gmail_address
GMAIL_TOKEN_JSON={"token":"...","refresh_token":"...","token_uri":"...","client_id":"...","client_secret":"...",...}
```

**Notes:**
- Paste the entire single-line JSON string from Step 2
- No quotes around the JSON in Railway's UI - paste the raw JSON
- Click "Add" after each variable
- **You do NOT need GMAIL_CREDENTIALS_JSON** - the token JSON has everything!

## Step 5: How Gmail OAuth Works on Railway

The app automatically detects it's running on Railway and loads credentials from environment variables:

```python
# 1. Load token from GMAIL_TOKEN_JSON environment variable
gmail_token_json = os.getenv('GMAIL_TOKEN_JSON')
token_data = json.loads(gmail_token_json)
creds = Credentials.from_authorized_user_info(token_data, SCOPES)

# 2. Auto-refresh if token is expired (no browser needed!)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())  # Silent refresh using refresh_token

# 3. Build Gmail service
service = build('gmail', 'v1', credentials=creds)
```

**Key features:**
- ✅ No browser needed on Railway
- ✅ Auto-refreshes expired tokens using refresh_token
- ✅ Works entirely headless
- ✅ Only needs GMAIL_TOKEN_JSON (has everything)

## Step 6: Configure the Procfile

Railway uses the `Procfile` to know how to run your app. It should contain:

```
worker: python3 main.py
```

This tells Railway to run `main.py` as a worker process (not a web server).

**Note:** The Procfile is already in the repository, so you don't need to create it.

## Step 7: Deploy and Monitor

### 7.1 Trigger deployment

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

### 7.2 Monitor logs

1. Go to your Railway project
2. Click on your service
3. Click "Deployments" tab
4. Click on the latest deployment
5. View real-time logs

You should see:
```
Loading Gmail credentials from GMAIL_TOKEN_JSON environment variable...
✓ Gmail token loaded from environment
✓ Gmail service initialized
🦞 OpenClaw Trade Assistant
✓ Supabase connection successful
Polling for new leads every 30 seconds...
```

### 7.3 Check for errors

Common issues:
- **Authentication failed:** Check GMAIL_TOKEN_JSON is set correctly (should be valid JSON)
- **Token refresh failed:** Regenerate token locally and update GMAIL_TOKEN_JSON
- **Database connection failed:** Check SUPABASE_URL and SUPABASE_KEY
- **Import errors:** Make sure requirements.txt is complete

## Step 8: Test the Deployment

### 8.1 Send a test email

Send a test lead email to your monitored Gmail address.

### 8.2 Check Railway logs

You should see:
```
✓ New lead detected: <subject>
✓ Lead parsed successfully
✓ Lead saved to database: <id>
✓ Reply generated (X words)
✓ Reply sent to <email>
```

### 8.3 Verify in Supabase

Check your Supabase dashboard - you should see the new lead in the `leads` table and messages in the `conversations` table.

## Step 9: Keep It Running

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
