# Gmail API Setup Guide

This guide walks you through setting up Gmail API access for OpenClaw Trade Assistant.

## Prerequisites

- Google account with Gmail
- Access to Google Cloud Console

## Step-by-Step Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name it: `OpenClaw Trade Assistant`
4. Click "Create"

### 2. Enable Gmail API

1. In your new project, go to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click on it and click "Enable"

### 3. Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Select "External" (unless you have a Google Workspace account)
3. Click "Create"
4. Fill in required fields:
   - **App name**: OpenClaw Trade Assistant
   - **User support email**: Your email
   - **Developer contact**: Your email
5. Click "Save and Continue"
6. On "Scopes" page, click "Add or Remove Scopes"
7. Add these scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.modify`
   - `https://www.googleapis.com/auth/gmail.send`
8. Click "Update" → "Save and Continue"
9. On "Test users" page, click "Add Users" and add your Gmail address
10. Click "Save and Continue"

### 4. Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Application type: **Desktop app**
4. Name: `OpenClaw Desktop Client`
5. Click "Create"
6. A dialog shows your Client ID and Client Secret
7. Click "OK" (we'll use them in the next step)

### 5. Add Credentials to .env File

1. In your project directory, create a `.env` file (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```
   GMAIL_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
   GMAIL_CLIENT_SECRET=your_client_secret_here
   GMAIL_USER_EMAIL=your_business_email@gmail.com
   ```

3. Save the file

### 6. Test the Connection

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the test script:
   ```bash
   python test_gmail_listener.py
   ```

3. On first run:
   - A browser window will open
   - Sign in with your Gmail account
   - You'll see a warning "Google hasn't verified this app"
   - Click "Advanced" → "Go to OpenClaw Trade Assistant (unsafe)"
   - Click "Continue"
   - Grant all requested permissions
   - You'll see "The authentication flow has completed"
   - Close the browser tab

4. A `token.json` file is created - this saves your authentication
5. Future runs won't require browser authentication

## Troubleshooting

### "Access blocked: This app's request is invalid"

- Make sure you added your email as a test user in OAuth consent screen
- Wait a few minutes after making changes in Google Cloud Console

### "redirect_uri_mismatch"

- The redirect URI should be `http://localhost`
- This is automatically configured in the code

### Token expired or invalid

- Delete `token.json` and run the test again
- You'll be prompted to re-authenticate

## Security Notes

- Never commit your `.env` file or `token.json` to git
- These are already in `.gitignore`
- Keep your Client Secret secure
- For production, use a service account instead of OAuth for user accounts

## Next Steps

Once authentication works, you can:
- Test polling your inbox with `test_gmail_listener.py`
- Send yourself test emails to see lead detection in action
- Move on to Step 3 (Lead Parser)
