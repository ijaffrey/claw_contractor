# Supabase Setup Guide

This guide walks you through setting up Supabase for OpenClaw Trade Assistant.

## Step 1: Create Supabase Account

1. Go to [https://supabase.com](https://supabase.com)
2. Click "Start your project"
3. Sign up with GitHub or email

## Step 2: Create New Project

1. Click "New Project"
2. Fill in:
   - **Name:** openclaw-trade-assistant
   - **Database Password:** (choose a strong password and save it)
   - **Region:** Choose closest to you (e.g., US East)
   - **Pricing Plan:** Free tier is perfect for getting started
3. Click "Create new project"
4. Wait 2-3 minutes for project to provision

## Step 3: Get Your API Credentials

1. In your project dashboard, click "Project Settings" (gear icon)
2. Go to "API" section
3. You'll see:
   - **Project URL** (e.g., `https://abcdefgh.supabase.co`)
   - **anon public** key (starts with `eyJ...`)

4. Copy both of these - you'll need them in a moment

## Step 4: Create Database Schema

1. In Supabase dashboard, click "SQL Editor" in left sidebar
2. Click "New query"
3. Open the file `schema.sql` from your project directory
4. Copy **all** the contents
5. Paste into the SQL Editor
6. Click "Run" (or press Cmd/Ctrl + Enter)
7. You should see success messages:
   - "Businesses table created" - count: 1
   - "Leads table created" - count: 0

This creates:
- `businesses` table
- `leads` table
- Indexes for performance
- Auto-update triggers
- Seeds test business "Mike's Plumbing"

## Step 5: Update .env File

Add your Supabase credentials to `.env`:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGc...your_anon_key_here
```

Replace with your actual values from Step 3.

## Step 6: Test Connection

Run the test script:

```bash
python3 test_database.py
```

You should see:
- ✓ Connection test passed
- ✓ Found 1 business (Mike's Plumbing)
- ✓ Lead inserted successfully
- ✓ All tests passed

## Troubleshooting

### "Connection failed"

- Check that SUPABASE_URL and SUPABASE_KEY are correct in `.env`
- Make sure the URL starts with `https://`
- Verify your project is fully provisioned (not still setting up)

### "No businesses found"

- Make sure you ran `schema.sql` in the SQL Editor
- Check for any error messages when running the schema
- Try running just the INSERT statement again

### "Permission denied"

- Make sure you're using the **anon** key, not the service_role key
- Check that Row Level Security (RLS) is disabled for testing (we'll enable it later)

## Optional: View Your Data

1. In Supabase dashboard, click "Table Editor"
2. You'll see `businesses` and `leads` tables
3. Click on each to view/edit data directly
4. This is helpful for debugging during development

## Next Steps

Once the tests pass, you're ready to move to Step 5 (Reply Generator)!

Your database now:
- Stores business profiles with brand voice
- Tracks all incoming leads
- Records lead status changes
- Links leads to businesses
- Auto-updates timestamps
