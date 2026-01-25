# 🚀 Zav Cloud Server - Railway Deployment Guide

**Deploy Zav to the cloud for 24/7 operation on Railway.app**

---

## Overview

This guide walks you through deploying the Zav Hospital Management System to Railway cloud hosting. Once deployed:

- ✅ **Always On**: System runs 24/7, never sleeps
- ✅ **Professional**: PostgreSQL database with automatic backups
- ✅ **Scalable**: Handles hospital growth from 100 to 10,000+ patients
- ✅ **Mobile**: Telegram bot accessible from any phone
- ✅ **Web UI**: Google Sheets for staff viewing/editing
- ✅ **Cost**: $5/month or FREE (with credit)

**System Architecture:**
```
Your Code on GitHub
    ↓
Railway Deployment (auto-deploys on push)
    ↓
    ├─ Flask Server (zav_cloud_server.py)
    ├─ PostgreSQL Database (auto-provisioned)
    └─ Telegram Bot Webhook

Connected to:
    ├─ Hospital Staff (Telegram Bot)
    ├─ Doctors (Google Sheets UI)
    └─ Admins (REST API)
```

---

## Prerequisites

You need:
1. **GitHub Account** - To store your code
2. **Railway Account** - Free, no credit card needed
3. **Telegram Bot Token** - From @BotFather (free, 2 minutes)
4. **Google Service Account** (optional) - For Google Sheets sync

**Time Required**: 15-20 minutes total

---

## Step 1: Prepare Your Code on GitHub

### 1.1 Create a GitHub Repository

If you don't have one already:
1. Go to https://github.com/new
2. Create repository: `zav-hospital` or similar
3. Clone locally

### 1.2 Add Zav Files to Your Repository

Make sure these files are in your GitHub repo:

```
zav-hospital/
├── zav_cloud_server.py          ← Main Flask app
├── zav_db_manager.py            ← Database manager (in cloud_server)
├── zav_sheets_sync.py           ← Google Sheets sync
├── zav_telegram_handler.py      ← Telegram bot commands
├── requirements.txt             ← Python dependencies
├── Procfile                     ← Railway config
└── .env.example                 ← Environment variables template
```

### 1.3 Commit and Push to GitHub

```bash
cd zav-hospital
git add .
git commit -m "Initial Zav cloud deployment setup"
git push origin main
```

---

## Step 2: Get Your Telegram Bot Token

This takes 2 minutes and allows the bot to send/receive messages.

### 2.1 Create Bot on Telegram

1. Open Telegram and search for: **@BotFather**
2. Click `/start`
3. Click `/newbot`
4. Choose a name: e.g., "Zav Hospital Bot"
5. Choose a username: e.g., "zav_hospital_bot" (must be unique)
6. Copy the token, looks like: `123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh`

### 2.2 Save Your Token

Save this token - you'll need it in Step 3.

---

## Step 3: Create Railway Account

### 3.1 Sign Up

1. Go to https://railway.app
2. Click "Start Building"
3. Sign up with GitHub (easiest)
4. Authorize Railway to access GitHub

### 3.2 Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Select your `zav-hospital` repository
4. Railway will auto-detect Procfile and deploy

---

## Step 4: Set Up PostgreSQL Database

### 4.1 Add PostgreSQL Service

In Railway dashboard:
1. Click your project
2. Click "+ Add Service"
3. Select "PostgreSQL"
4. Railway auto-provisions a database

### 4.2 Get Connection String

1. Click the PostgreSQL service
2. Go to "Variables"
3. Find `DATABASE_URL` - looks like:
   ```
   postgres://username:password@hostname:5432/railway
   ```
4. Copy this value (you'll use it next)

---

## Step 5: Configure Environment Variables

### 5.1 In Railway Dashboard

1. Go to your Flask app service
2. Click "Variables"
3. Add these environment variables:

| Variable | Value | Example |
|----------|-------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgres://user:pass@host/db` |
| `TELEGRAM_BOT_TOKEN` | Your bot token from Step 2 | `123456:ABC...` |
| `PORT` | 8000 (default) | `8000` |
| `DEBUG` | False for production | `False` |
| `GOOGLE_SHEETS_KEY` | (Optional) Base64 Google credentials | `eyJh...` |

### 5.2 Save Variables

Railway will restart the app automatically with new variables.

---

## Step 6: Configure Telegram Webhook

Once your app is deployed, Railway gives you a URL like: `https://zav-hospital.up.railway.app`

### 6.1 Set Webhook

Run this command (replace with your values):

```bash
curl -X POST \
  https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook \
  -d url=https://zav-hospital.up.railway.app/webhook/telegram
```

Replace `YOUR_BOT_TOKEN` with your actual token from Step 2.

### 6.2 Verify Webhook is Set

```bash
curl -X GET \
  https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo
```

You should see status: `pending` or `ok` (not `failed`).

---

## Step 7: Test Your Deployment

### 7.1 Test API Endpoints

Check if your server is running:

```bash
curl https://zav-hospital.up.railway.app/api/health
```

You should get:
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2025-12-18T10:30:00"
}
```

### 7.2 Test Telegram Bot

1. Find your bot on Telegram (search for the username from Step 2)
2. Click `/start`
3. Try `/alerts`, `/beds`, `/patients`, etc.

Bot should respond with formatted data!

### 7.3 Test REST API

Get list of patients:
```bash
curl https://zav-hospital.up.railway.app/api/patients
```

Create a patient:
```bash
curl -X POST https://zav-hospital.up.railway.app/api/patients \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PAT001",
    "name": "John Doe",
    "admission_date": "2025-12-18",
    "status": "active"
  }'
```

---

## Step 8: Set Up Google Sheets (Optional)

### 8.1 Create Google Service Account

1. Go to https://console.cloud.google.com/
2. Create new project: "Zav Hospital"
3. Enable "Google Sheets API"
4. Create "Service Account" credentials
5. Download JSON file

### 8.2 Create Google Sheets

1. Create new Google Sheet: "Zav Patient Data"
2. Share with service account email from JSON file
3. Copy Sheet URL

### 8.3 Configure in Railway

1. Base64 encode your JSON file:
   ```bash
   base64 -w 0 < service_account.json
   ```

2. In Railway Variables, set:
   - `GOOGLE_SHEETS_KEY`: (the base64 output)
   - `GOOGLE_SHEETS_URL`: (your sheet URL)

3. Trigger sync:
   ```bash
   curl -X POST https://zav-hospital.up.railway.app/sync/sheets
   ```

---

## Step 9: Customize and Extend

### 9.1 Add More Hospital Data

Edit `zav_cloud_server.py` to add more endpoints for:
- Doctor assignments
- Operation schedules
- Lab results
- Medication inventory

### 9.2 Integrate with Existing Systems

Connect to your EMR or hospital management system:
- Implement HL7 message parsing
- Add FHIR API compatibility
- Create two-way sync with your EMR

### 9.3 Add More Telegram Commands

Edit `zav_telegram_handler.py` to add:
- Custom alert routing
- Shift change notifications
- Daily briefing reports
- Staff scheduling

---

## Monitoring and Maintenance

### View Logs

In Railway dashboard:
1. Click your app
2. Click "Logs"
3. See real-time logs of requests and errors

### Monitor Database

In Railway dashboard:
1. Click PostgreSQL service
2. See storage usage, connections
3. View backups (automatic daily)

### Update Code

Just push to GitHub and Railway auto-deploys:
```bash
git add .
git commit -m "Add new features"
git push origin main
```

---

## Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| Railway Free Tier | $0 | Limited to $5/month usage |
| Railway $5 credit | $5/month | Includes Flask app + PostgreSQL |
| PostgreSQL | Included | No extra cost with Railway |
| Telegram Bot | $0 | Free service |
| Google Sheets | $0 | Free with Google account |
| **Total** | **$0-5/month** | ✅ Very affordable |

---

## Troubleshooting

### Problem: Telegram bot not responding

**Solution:**
1. Check webhook status:
   ```bash
   curl https://api.telegram.org/botTOKEN/getWebhookInfo
   ```

2. If status is "failed", check Railway logs for errors

3. Re-set webhook:
   ```bash
   curl -X POST https://api.telegram.org/botTOKEN/setWebhook \
     -d url=https://zav-hospital.up.railway.app/webhook/telegram
   ```

### Problem: "Database not available"

**Solution:**
1. Check DATABASE_URL variable is set in Railway
2. Check PostgreSQL service is running (green status)
3. Check logs for connection errors

### Problem: API returns 404

**Solution:**
1. Check URL is correct: `https://zav-hospital.up.railway.app/api/patients`
2. Check Procfile is correct
3. Check Flask app is running (Railway logs)

### Problem: Out of memory or slow performance

**Solution:**
1. Upgrade Railway plan (click service, select larger tier)
2. Add connection pooling to database
3. Implement Redis caching

---

## Next Steps

After successful deployment:

1. **Share Telegram Bot** with your hospital staff
   - They can add `@zav_hospital_bot` (your bot username)
   - They get instant access to patient data

2. **Share Google Sheets** with doctors
   - They can view/edit patient data in familiar format
   - Changes sync back to database

3. **Set Up Alerts** in database
   - Add critical patient alerts
   - Bot sends notifications automatically

4. **Integrate with Your EMR**
   - Sync patient data from your hospital system
   - Zav provides real-time clinical insights

5. **Monitor and Scale**
   - Watch performance metrics
   - Add more features as needed
   - Upgrade when you hit limits

---

## Advanced Configuration

### Custom Domain

Railway lets you use a custom domain instead of `.up.railway.app`:

1. In Railway, click "Settings"
2. Add "Custom Domain": `zav.yourhospital.com`
3. Update DNS records (Railway provides instructions)
4. Update Telegram webhook with new domain

### SSL/HTTPS Certificates

Railway includes free SSL certificates automatically.
Your `https://zav-hospital.up.railway.app` is secure out of the box.

### Backup and Recovery

PostgreSQL backups are automatic:
- Daily backups stored in Railway
- 7-day retention
- One-click restore in Railway dashboard

### Horizontal Scaling

If your hospital grows:
1. Upgrade Railway plan
2. Add more worker processes in Procfile
3. Enable database connection pooling
4. Add Redis cache layer

---

## Support and Documentation

**Files included:**
- `zav_cloud_server.py` - Main Flask application
- `zav_sheets_sync.py` - Google Sheets integration
- `zav_telegram_handler.py` - Telegram bot logic
- `requirements.txt` - Python dependencies
- `Procfile` - Railway deployment config

**Example API Calls:**
```bash
# List all patients
curl https://zav-hospital.up.railway.app/api/patients

# Get specific patient
curl https://zav-hospital.up.railway.app/api/patients/PAT001

# Get patient equipment
curl https://zav-hospital.up.railway.app/api/equipment/PAT001

# Create alert
curl -X POST https://zav-hospital.up.railway.app/api/alerts \
  -H "Content-Type: application/json" \
  -d '{"alert_id":"ALR001","patient_id":"PAT001","severity":"warning","message":"Patient overdue for consultation"}'
```

---

## Summary

You now have a **production-ready, 24/7, always-on hospital management system** with:

✅ **24/7 Operation** - Runs continuously on Railway cloud
✅ **Mobile Access** - Telegram bot for staff on-the-go
✅ **Web Interface** - Google Sheets for easy data viewing
✅ **Professional Database** - PostgreSQL with automatic backups
✅ **Minimal Cost** - $5/month or FREE
✅ **Easy Updates** - Just push to GitHub, auto-deployed

🎉 **Your Zav system is now live!**

---

**Questions? Issues?**

Check Railway logs: `Railway Dashboard → Your App → Logs`

---

**Deployed**: December 18, 2025
**Version**: 1.0
**Status**: Production Ready 🚀
