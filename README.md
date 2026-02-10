# 🚀 Telegram Auto Reaction SaaS

[![Production Ready](https://img.shields.io/badge/Production-Ready-brightgreen.svg)](https://github.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-blue.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12+-yellow.svg)](https://python.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-green.svg)](https://mongodb.com)

**Production-grade Telegram auto-reaction platform with Apple-level UI and real-time analytics.**

---

## ✨ Features

### 🤖 Telegram Bot
- ✅ Auto-react to channels, groups, and forwarded messages
- ✅ Multiple emoji modes (random, fixed, sequential)
- ✅ Configurable delays and anti-flood protection
- ✅ Automatic retry with exponential backoff
- ✅ FloodWait handling with smart scheduling
- ✅ Owner commands for user management

### 🌐 Web Dashboard
- ✅ Apple-inspired glassmorphism UI
- ✅ Real-time WebSocket analytics
- ✅ Live reaction metrics
- ✅ Chat management interface
- ✅ User approval system
- ✅ Role-based access control (RBAC)
- ✅ Dynamic anime backgrounds

### 📊 Analytics Engine
- ✅ Total reactions counter
- ✅ Reactions per second
- ✅ Active chats monitoring
- ✅ Flood wait tracking
- ✅ Error rate calculations
- ✅ Emoji usage heatmap
- ✅ Hourly statistics
- ✅ Per-chat analytics

### 🔐 Security
- ✅ JWT authentication with rotation
- ✅ Bcrypt password hashing
- ✅ MongoDB-based rate limiting
- ✅ Input sanitization
- ✅ CORS protection
- ✅ Security headers
- ✅ Owner approval system

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     User Browser                         │
│            (Next.js + Tailwind + Framer Motion)         │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTPS / WSS
┌──────────────────▼──────────────────────────────────────┐
│                  FastAPI Backend                         │
│  ┌──────────┬──────────┬──────────┬─────────────────┐  │
│  │   Auth   │ WebSocket│Analytics │  Admin Manager  │  │
│  │ Manager  │ Manager  │  Engine  │                 │  │
│  └──────────┴──────────┴──────────┴─────────────────┘  │
└──────────────────┬──────────────────────────────────────┘
                   │
         ┌─────────┴──────────┐
         │                     │
┌────────▼────────┐   ┌───────▼──────────┐
│   MongoDB       │   │  Pyrogram Bot    │
│ (All Data)      │   │ (Telegram API)   │
│                 │   │                  │
│ • Users         │   │ • Reactions      │
│ • Chats         │   │ • Commands       │
│ • Reactions     │   │ • FloodWait      │
│ • Analytics     │   │                  │
│ • Cache         │   │                  │
│ • Rate Limits   │   │                  │
└─────────────────┘   └──────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- MongoDB 6.0+
- Node.js 20+
- Telegram API credentials ([Get here](https://my.telegram.org))
- Bot Token ([Create via @BotFather](https://t.me/BotFather))

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/telegram-reaction-saas.git
cd telegram-reaction-saas
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp ../.env.example .env

# Edit .env with your credentials
nano .env
```

**Required Environment Variables:**

```env
# MongoDB (Get from MongoDB Atlas)
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/telegram_reaction_saas

# JWT Secret (Generate with: openssl rand -base64 32)
JWT_SECRET=your_secure_random_string_here

# Telegram Credentials
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token

# Owner Configuration
OWNER_TELEGRAM_ID=your_telegram_user_id
OWNER_USERNAME=admin
OWNER_PASSWORD=your_secure_password
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Configure API URL
# Edit package.json or .env.local with backend URL
```

### 4. Run Application

**Backend:**
```bash
cd backend
python main.py
```

**Frontend:**
```bash
cd frontend
npm run dev
```

Access dashboard at: `http://localhost:3000`

---

## 🌐 Render.com Deployment

### Step 1: Prepare MongoDB

1. Create a **MongoDB Atlas** account ([https://mongodb.com/cloud/atlas](https://mongodb.com/cloud/atlas))
2. Create a new cluster (Free tier available)
3. Create a database user
4. Whitelist all IPs (0.0.0.0/0) for Render.com
5. Copy your connection string

### Step 2: Deploy Backend

1. Create new **Web Service** on Render.com
2. Connect your GitHub repository
3. Configure:
   - **Name:** `telegram-reaction-backend`
   - **Environment:** `Python 3`
   - **Build Command:** `cd backend && pip install -r requirements.txt`
   - **Start Command:** `cd backend && python main.py`
   - **Plan:** Free or paid

4. Add Environment Variables:
   ```
   MONGODB_URL=your_mongodb_atlas_url
   JWT_SECRET=your_generated_secret
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_BOT_TOKEN=your_bot_token
   OWNER_TELEGRAM_ID=your_telegram_id
   OWNER_USERNAME=admin
   OWNER_PASSWORD=your_password
   PORT=8000
   CORS_ORIGINS=https://your-frontend.onrender.com
   ```

5. Deploy and copy the service URL (e.g., `https://telegram-reaction-backend.onrender.com`)

### Step 3: Deploy Frontend

1. Create new **Static Site** on Render.com
2. Configure:
   - **Name:** `telegram-reaction-frontend`
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Publish Directory:** `frontend/out` or `frontend/.next`
   
3. Add Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://telegram-reaction-backend.onrender.com
   NEXT_PUBLIC_WS_URL=wss://telegram-reaction-backend.onrender.com
   ```

4. Deploy

### Step 4: Update Backend CORS

Update backend environment variable:
```
CORS_ORIGINS=https://your-frontend.onrender.com
```

### Step 5: Test Deployment

1. Visit your frontend URL
2. Login with owner credentials
3. Check bot status in dashboard
4. Add bot to a channel/group
5. Monitor real-time analytics

---

## 📱 Telegram Bot Commands

### Owner Commands

```
/start       - Display welcome message with inline buttons
/adduser     - Create new dashboard user (owner only)
/approve     - Approve pending user (owner only)
/pending     - List pending users (owner only)
/stats       - Show bot statistics
```

### Example Usage

```bash
# Add new user
/adduser john SecurePass123

# Approve user
/approve john

# Check pending
/pending
```

---

## 🎨 Frontend Features

### Landing Page
- Physics-based hero animation
- Live stats counter
- Feature grid with glassmorphism
- Call-to-action sections

### Dashboard
- Real-time analytics charts
- Live activity feed
- Emoji configuration
- Delay sliders
- Chat management
- User approval interface

### UI Components
- Frosted glass panels
- Smooth transitions
- Dynamic anime backgrounds
- Physics animations
- Gradient meshes

---

## 🔧 Configuration

### Bot Settings

Configure via dashboard or MongoDB:

```json
{
  "auto_react": true,
  "default_emojis": ["❤️", "🔥", "👍", "😍", "✨"],
  "default_delay_min": 1,
  "default_delay_max": 5,
  "max_retries": 3,
  "retry_delay": 60,
  "flood_wait_multiplier": 1.5,
  "enable_sentiment": false
}
```

### Chat Configuration

```json
{
  "chat_id": -1001234567890,
  "chat_title": "My Channel",
  "enabled": true,
  "reaction_mode": "random",
  "emojis": ["❤️", "🔥", "👍"],
  "delay_min": 1,
  "delay_max": 5,
  "react_to_media": true,
  "react_to_text": true,
  "react_to_forwards": false
}
```

---

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `GET /api/v1/auth/me` - Get current user

### Users
- `GET /api/v1/users` - List all users
- `POST /api/v1/users/{username}/approve` - Approve user
- `PUT /api/v1/users/{username}/role` - Update role
- `DELETE /api/v1/users/{username}` - Delete user

### Chats
- `GET /api/v1/chats` - List configured chats
- `POST /api/v1/chats` - Add chat
- `PUT /api/v1/chats/{chat_id}` - Update chat
- `DELETE /api/v1/chats/{chat_id}` - Delete chat

### Analytics
- `GET /api/v1/stats` - Get all statistics
- `GET /api/v1/stats/chat/{chat_id}` - Get chat stats
- `GET /api/v1/stats/daily` - Get daily summary
- `GET /api/v1/stats/top-chats` - Get top chats

### WebSocket
- `WS /ws` - Real-time updates

---

## 🛡️ Security Best Practices

1. **Never commit `.env` files**
2. **Use strong JWT secrets** (32+ characters)
3. **Enable MongoDB authentication**
4. **Whitelist only necessary IPs**
5. **Use HTTPS in production**
6. **Regularly rotate secrets**
7. **Monitor rate limits**
8. **Review user access logs**

---

## 🐛 Troubleshooting

### Bot Not Starting

```bash
# Check logs
tail -f backend/logs/*.log

# Verify Telegram credentials
# Test with: https://my.telegram.org/auth

# Check MongoDB connection
mongosh "your_connection_string"
```

### WebSocket Connection Issues

```bash
# Ensure CORS is configured
# Check browser console for errors
# Verify WSS protocol for HTTPS sites
```

### FloodWait Errors

- Bot automatically handles FloodWait
- Adjust delay settings if frequent
- Monitor flood_waits in analytics

---

## 📈 Performance Optimization

### MongoDB Indexes

All indexes are created automatically on startup:
- `users`: username, telegram_id, status, role
- `reactions`: chat_id, timestamp, emoji, status
- `chats`: chat_id, enabled
- `analytics`: timestamp, metric_type

### Rate Limiting

- Login: 5 requests per 5 minutes
- API: 60 requests per minute
- Wallpaper: 10 requests per minute

### Caching

- Wallpapers: 1 hour TTL
- Implemented via MongoDB cache collection

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📜 License

MIT License - See LICENSE file for details

---

## 👨‍💻 Developer

**Mr. Dhanpal Sharma**
- Telegram: [@MrDhanpalSharma](https://t.me/MrDhanpalSharma)
- Community: [@THEUPDATEDGUYS](https://t.me/THEUPDATEDGUYS)

---

## 🙏 Acknowledgments

- Powered by **The Updated Guys** 🌟
- Built with FastAPI, Pyrogram, Next.js
- Inspired by Linear, Notion, and Apple's design language

---

## 📞 Support

For support, join our Telegram community: [@THEUPDATEDGUYS](https://t.me/THEUPDATEDGUYS)

---

Made with ❤️ by The Updated Guys
