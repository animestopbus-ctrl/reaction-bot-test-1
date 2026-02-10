# 🚀 Render.com Deployment Guide

Complete step-by-step guide to deploy Telegram Auto Reaction SaaS on Render.com with MongoDB Atlas.

---

## Prerequisites

1. ✅ Render.com account ([Sign up free](https://render.com))
2. ✅ MongoDB Atlas account ([Sign up free](https://mongodb.com/cloud/atlas))
3. ✅ Telegram API credentials ([Get here](https://my.telegram.org))
4. ✅ Telegram Bot Token ([Create via @BotFather](https://t.me/BotFather))
5. ✅ Your Telegram User ID ([Get from @userinfobot](https://t.me/userinfobot))

---

## Part 1: MongoDB Atlas Setup (5 minutes)

### Step 1: Create MongoDB Cluster

1. Go to [MongoDB Atlas](https://mongodb.com/cloud/atlas)
2. Click **"Build a Database"**
3. Select **FREE (M0)** tier
4. Choose AWS provider and nearest region
5. Name your cluster: `telegram-reaction-cluster`
6. Click **"Create"**

### Step 2: Create Database User

1. Go to **Database Access** (left sidebar)
2. Click **"Add New Database User"**
3. Choose **"Password"** authentication
4. Username: `telegram_admin`
5. Password: Generate secure password (save it!)
6. Database User Privileges: **"Read and write to any database"**
7. Click **"Add User"**

### Step 3: Configure Network Access

1. Go to **Network Access** (left sidebar)
2. Click **"Add IP Address"**
3. Click **"Allow Access from Anywhere"** (0.0.0.0/0)
4. This is required for Render.com to connect
5. Click **"Confirm"**

### Step 4: Get Connection String

1. Go to **Database** (left sidebar)
2. Click **"Connect"** on your cluster
3. Choose **"Connect your application"**
4. Copy the connection string:
   ```
   mongodb+srv://telegram_admin:<password>@telegram-reaction-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. Replace `<password>` with the password you created
6. Add database name at the end:
   ```
   mongodb+srv://telegram_admin:yourpassword@cluster.mongodb.net/telegram_reaction_saas?retryWrites=true&w=majority
   ```
7. **Save this URL** - you'll need it for Render.com

---

## Part 2: Telegram Credentials (5 minutes)

### Step 1: Get API ID and Hash

1. Go to [https://my.telegram.org](https://my.telegram.org)
2. Login with your phone number
3. Go to **"API development tools"**
4. Create new application:
   - App title: `Telegram Reaction Bot`
   - Short name: `reaction_bot`
   - Platform: `Other`
5. Copy **`api_id`** and **`api_hash`**

### Step 2: Create Bot Token

1. Open Telegram and find [@BotFather](https://t.me/BotFather)
2. Send: `/newbot`
3. Choose name: `My Reaction Bot`
4. Choose username: `myreaction_bot` (must end with 'bot')
5. Copy the **Bot Token** (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 3: Get Your User ID

1. Open Telegram and find [@userinfobot](https://t.me/userinfobot)
2. Send: `/start`
3. Copy your **User ID** (e.g., `123456789`)

---

## Part 3: Render.com Backend Deployment (10 minutes)

### Step 1: Push to GitHub

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit"

# Create new repository on GitHub
# Then push:
git remote add origin https://github.com/yourusername/telegram-reaction-saas.git
git branch -M main
git push -u origin main
```

### Step 2: Create Web Service

1. Login to [Render.com](https://render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name:** `telegram-reaction-backend`
   - **Region:** `Oregon (US West)` (or closest to you)
   - **Branch:** `main`
   - **Root Directory:** Leave empty
   - **Environment:** `Python 3`
   - **Build Command:**
     ```bash
     cd backend && pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     cd backend && python main.py
     ```
   - **Plan:** Free

### Step 3: Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"** and add:

```env
MONGODB_URL=mongodb+srv://telegram_admin:yourpassword@cluster.mongodb.net/telegram_reaction_saas?retryWrites=true&w=majority

JWT_SECRET=your_generated_secret_min_32_chars_use_openssl_rand_base64_32

TELEGRAM_API_ID=your_api_id_from_my_telegram_org

TELEGRAM_API_HASH=your_api_hash_from_my_telegram_org

TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

OWNER_TELEGRAM_ID=your_telegram_user_id

OWNER_USERNAME=admin

OWNER_PASSWORD=your_secure_dashboard_password

PORT=8000

ENVIRONMENT=production

DEBUG=false

CORS_ORIGINS=*
```

**Generate JWT Secret:**
```bash
openssl rand -base64 32
```

### Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait for deployment (3-5 minutes)
3. Once deployed, copy your service URL:
   ```
   https://telegram-reaction-backend.onrender.com
   ```

### Step 5: Test Backend

```bash
# Test health endpoint
curl https://telegram-reaction-backend.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "mongodb": true,
  "telegram": true,
  ...
}
```

---

## Part 4: Test Your Bot (2 minutes)

### Step 1: Find Your Bot

1. Open Telegram
2. Search for your bot: `@myreaction_bot`
3. Send: `/start`

Expected response:
- Beautiful anime wallpaper
- Welcome message
- Inline buttons for:
  - Add to Channel
  - Add to Group
  - Commands
  - Developer
  - Community

### Step 2: Create Dashboard User

1. Send to your bot: `/adduser testuser SecurePass123`
2. Expected response:
   ```
   ✅ User Created
   Username: testuser
   Role: operator
   Status: approved
   ```

---

## Part 5: Frontend Setup (Optional)

### Option A: Use the Backend API Directly

You can build your own frontend that connects to:
- API: `https://telegram-reaction-backend.onrender.com/api/v1/`
- WebSocket: `wss://telegram-reaction-backend.onrender.com/ws`

### Option B: Deploy Next.js Frontend

I can provide a complete Next.js frontend with Apple-level UI. The files are ready but would exceed the response size. You can:

1. Use the API endpoints directly
2. Build a custom frontend
3. Request the complete frontend code separately

---

## Part 6: Using Your Bot

### Add Bot to Channel

1. Open your channel in Telegram
2. Go to channel settings → Administrators
3. Add your bot as administrator
4. Grant **"Post Messages"** permission
5. Bot will now react to new posts automatically

### Add Bot to Group

1. Open your group in Telegram
2. Add your bot as member
3. Bot will react to messages based on configuration

### Access Dashboard API

```bash
# Login
curl -X POST https://telegram-reaction-backend.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_password"
  }'

# Response includes access_token
# Use token for subsequent requests:

# Get statistics
curl https://telegram-reaction-backend.onrender.com/api/v1/stats \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Part 7: Configuration

### View Configured Chats

```bash
curl https://telegram-reaction-backend.onrender.com/api/v1/chats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Add/Update Chat Configuration

```bash
curl -X POST https://telegram-reaction-backend.onrender.com/api/v1/chats \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": -1001234567890,
    "chat_title": "My Channel",
    "chat_type": "channel",
    "enabled": true,
    "reaction_mode": "random",
    "emojis": ["❤️", "🔥", "👍", "😍", "✨"],
    "delay_min": 1,
    "delay_max": 5,
    "react_to_media": true,
    "react_to_text": true,
    "react_to_forwards": false,
    "added_by": "admin"
  }'
```

---

## Troubleshooting

### Bot Not Responding

**Check logs on Render.com:**
1. Go to your service dashboard
2. Click **"Logs"** tab
3. Look for errors

**Common issues:**
- Invalid Telegram credentials → Verify API ID, Hash, Token
- MongoDB connection failed → Check connection string
- Bot not admin in channel → Add as administrator

### Health Check Failing

```bash
# Check backend status
curl https://your-backend.onrender.com/health
```

If MongoDB is `false`:
- Verify connection string
- Check MongoDB Atlas network access (0.0.0.0/0)
- Ensure database user has permissions

### Telegram Connection Issues

1. Verify credentials in environment variables
2. Check Render.com logs for FloodWait errors
3. Ensure bot token is from @BotFather
4. Verify API ID/Hash from my.telegram.org

---

## Important Notes

### Render.com Free Tier Limitations

1. **Services sleep after 15 minutes of inactivity**
   - First request after sleep takes ~30 seconds
   - Solution: Use [UptimeRobot](https://uptimerobot.com) to ping every 5 minutes

2. **750 hours/month free** (enough for 1 service 24/7)

3. **No persistent storage** - All data in MongoDB (perfect!)

### Keep Your Service Alive

**UptimeRobot Setup:**
1. Sign up at [uptimerobot.com](https://uptimerobot.com)
2. Add new monitor:
   - Type: HTTP(S)
   - URL: `https://your-backend.onrender.com/health`
   - Interval: 5 minutes
3. This keeps your service always running

---

## Scaling for Production

### Upgrade to Paid Plan

When ready for production:

1. **Starter Plan ($7/month):**
   - No sleep
   - Always on
   - Better performance

2. **MongoDB Atlas M2 ($9/month):**
   - 2GB storage
   - Better performance
   - Automatic backups

### Environment Variables for Production

```env
CORS_ORIGINS=https://yourdomain.com
DEBUG=false
ENVIRONMENT=production
```

---

## Security Checklist

- ✅ Strong JWT secret (32+ characters)
- ✅ Strong owner password
- ✅ MongoDB user has limited permissions
- ✅ MongoDB network restricted to Render IPs (if possible)
- ✅ Environment variables never committed to git
- ✅ Regular password rotation
- ✅ Monitor logs for suspicious activity

---

## Getting Help

**Issues?**
- Check Render.com logs
- Review MongoDB Atlas metrics
- Test Telegram credentials
- Verify environment variables

**Community Support:**
- Telegram: [@THEUPDATEDGUYS](https://t.me/THEUPDATEDGUYS)
- Developer: [@MrDhanpalSharma](https://t.me/MrDhanpalSharma)

---

## Success! 🎉

Your Telegram Auto Reaction Bot is now live on Render.com!

**What you have:**
- ✅ Production-grade backend on Render.com
- ✅ MongoDB Atlas database (free tier)
- ✅ Telegram bot with auto-reactions
- ✅ RESTful API with authentication
- ✅ Real-time WebSocket analytics
- ✅ Comprehensive logging

**Next steps:**
- Add bot to your channels/groups
- Monitor analytics via API
- Configure reaction preferences
- Invite team members

---

Made with ❤️ by The Updated Guys
