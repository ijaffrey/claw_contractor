# Debugging the Conversation Loop

This guide helps diagnose issues with the multi-message conversation loop in Railway logs.

## What to Look For in Railway Logs

### 1. New Lead Detection

When a NEW lead arrives, you should see:

```
🔍 DEBUG: Processing email
   Email ID:   abc123
   Thread ID:  thread_xyz
   From:       customer@example.com
   Subject:    Need plumbing help

🔍 DEBUG: Checking if email ID already processed...
🔍 DEBUG: Email ID not found - this is a new email

🔍 DEBUG: Checking for existing lead by thread_id: thread_xyz
🔍 DEBUG (database.py): Looking up lead by thread_id: thread_xyz
🔍 DEBUG (database.py): Thread lookup response
   Found 0 leads
   No lead found with thread_id: thread_xyz

🔍 DEBUG: No existing lead found - this is a NEW LEAD

📋 Parsing new lead data...
```

### 2. Conversation Storage (New Lead)

You should see messages being stored:

```
💬 Storing initial message in conversation history...
🔍 DEBUG: Attempting to store customer message
   Lead ID: lead-uuid
   Role: customer
   Message length: 150 chars

🔍 DEBUG (database.py): Inserting conversation message
   lead_id: lead-uuid
   role: customer
   message length: 150
   email_id: email123

🔍 DEBUG (database.py): Response received
   response.data: [{'id': 'conv-uuid', ...}]

✓ Conversation message added: customer - 150 chars
🔍 DEBUG: Customer message stored successfully (ID: conv-uuid)
```

**If conversations table is empty, look for:**
- ⚠️ WARNING: Failed to store customer message
- ✗ Error inserting conversation message
- Check if migration was run in Supabase

### 3. Reply Detection

When a customer REPLIES to an existing thread, you should see:

```
🔍 DEBUG: Processing email
   Email ID:   reply456
   Thread ID:  thread_xyz  ← SAME as original
   From:       customer@example.com
   Subject:    Re: Need plumbing help

🔍 DEBUG: Checking if email ID already processed...
🔍 DEBUG: Email ID not found - this is a new email

🔍 DEBUG: Checking for existing lead by thread_id: thread_xyz
🔍 DEBUG (database.py): Looking up lead by thread_id: thread_xyz
🔍 DEBUG (database.py): Thread lookup response
   Found 1 leads  ← FOUND IT!
   Lead ID: lead-uuid
   Customer: John Doe
   Qualification step: 1

🔍 DEBUG: Found existing lead! This is a REPLY
   Lead ID: lead-uuid
   Customer: John Doe
   Current step: 1

💬 Processing REPLY to existing lead...
```

**If replies are not detected, look for:**
- Thread ID mismatch (different thread_ids)
- "Found 0 leads" when you expect to find one
- Check if the original lead was actually stored

### 4. Conversation History Loading

When processing a reply:

```
📜 Loading conversation history...
🔍 DEBUG: Loaded 2 messages from conversation history
🔍 DEBUG: First message role: customer
🔍 DEBUG: Last message role: assistant
   Total messages: 2
```

**If history is empty when it shouldn't be:**
- ⚠️ WARNING: Conversation history is EMPTY - this is unexpected!
- Check conversations table in Supabase
- Verify lead_id matches

### 5. Qualification Step Progression

```
🎯 Qualification sequence:
   Current step: 1 - urgency
   Next step:    2 - job_details
```

## Common Issues and Solutions

### Issue: Conversations table is empty

**Diagnosis:**
```
⚠️ WARNING: Failed to store customer message in conversations table
```

**Solution:**
1. Check Railway logs for database errors
2. Run migration in Supabase: `migration_add_conversations.sql`
3. Verify table exists: `SELECT * FROM conversations LIMIT 1`
4. Check Supabase API key permissions

### Issue: Replies not detected

**Diagnosis:**
```
Found 0 leads
No lead found with thread_id: xyz
🔍 DEBUG: No existing lead found - this is a NEW LEAD
```

**Solution:**
1. Verify thread_id is stored when creating lead
2. Check if thread_id changes between emails
3. Verify `email_thread_id` column exists in leads table
4. Check Supabase index on `email_thread_id`

### Issue: Thread ID mismatch

**Symptoms:**
- Original email has thread_id: "abc123"
- Reply has thread_id: "def456" (different!)

**Cause:**
Gmail assigns new thread IDs when:
- Subject line changes significantly
- Long delay between messages
- Email client doesn't preserve threading headers

**Solution:**
- Not much we can do - Gmail controls threading
- Consider matching by customer_email as fallback

### Issue: Multiple leads for same thread

**Diagnosis:**
```
Found 2 leads  ← Should only be 1!
```

**Solution:**
This shouldn't happen, but if it does:
1. Check for duplicate email processing
2. Verify deduplication logic is working
3. May need to add UNIQUE constraint on thread_id

## Checking Supabase Directly

### Verify conversations table exists

```sql
SELECT COUNT(*) FROM conversations;
```

Should return a count, not an error.

### Check if messages are being stored

```sql
SELECT
  c.id,
  c.role,
  c.created_at,
  LEFT(c.message, 50) as message_preview,
  l.customer_name
FROM conversations c
JOIN leads l ON c.lead_id = l.id
ORDER BY c.created_at DESC
LIMIT 10;
```

### Find leads with their thread IDs

```sql
SELECT
  id,
  customer_name,
  email_thread_id,
  qualification_step,
  status,
  created_at
FROM leads
ORDER BY created_at DESC
LIMIT 10;
```

### Check for orphaned conversations

```sql
SELECT COUNT(*)
FROM conversations c
LEFT JOIN leads l ON c.lead_id = l.id
WHERE l.id IS NULL;
```

Should return 0.

## Railway Deployment Checklist

After deploying with debug logs:

1. ✅ Check Railway build succeeded
2. ✅ Check Railway service is running
3. ✅ Send test email (new lead)
4. ✅ Check logs for conversation storage
5. ✅ Check Supabase conversations table
6. ✅ Reply to test email
7. ✅ Check logs for reply detection
8. ✅ Verify follow-up was sent
9. ✅ Check conversations table for all messages

## Removing Debug Logs

Once issue is resolved, search for:
- `🔍 DEBUG`
- `⚠️  WARNING`

And remove excessive logging (keep essential logs).
