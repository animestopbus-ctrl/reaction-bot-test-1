import asyncio
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReactionTypeEmoji
from pyrogram.errors import FloodWait, RPCError
from LastPerson07.config import settings
from LastPerson07.database import db
from LastPerson07.logger import logger
from LastPerson07.utils import exponential_backoff
from LastPerson07.auth import auth_manager


class TelegramBot:
    """Production-grade Telegram reaction bot"""
    
    def __init__(self):
        self.app: Optional[Client] = None
        self.is_running = False
        self.start_time = datetime.utcnow()
        self.stats = {
            "total_reactions": 0,
            "flood_waits": 0,
            "errors": 0,
            "active_chats": set(),
        }
    
    async def initialize(self):
        """Initialize Pyrogram client"""
        self.app = Client(
            name=settings.TELEGRAM_SESSION_NAME,
            api_id=settings.TELEGRAM_API_ID,
            api_hash=settings.TELEGRAM_API_HASH,
            bot_token=settings.TELEGRAM_BOT_TOKEN,
            workdir="sessions",
        )
        
        await self.app.start()
        self.is_running = True
        
        logger.info("Telegram bot started successfully")
        
        await self._create_owner_account()
        
        self._register_handlers()
    
    async def stop(self):
        """Stop the bot"""
        if self.app:
            await self.app.stop()
            self.is_running = False
            logger.info("Telegram bot stopped")
    
    async def _create_owner_account(self):
        """Create owner account if it doesn't exist"""
        try:
            existing_owner = await db.get_collection("users").find_one(
                {"telegram_id": settings.OWNER_TELEGRAM_ID}
            )
            
            if not existing_owner:
                await auth_manager.create_user(
                    username=settings.OWNER_USERNAME,
                    password=settings.OWNER_PASSWORD,
                    telegram_id=settings.OWNER_TELEGRAM_ID,
                    role="owner",
                    status="approved",
                )
                logger.info("Owner account created")
        except Exception as e:
            logger.error(f"Failed to create owner account: {str(e)}")
    
    def _register_handlers(self):
        """Register message handlers"""
        
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_handler(client: Client, message: Message):
            await self._handle_start(message)
        
        @self.app.on_message(filters.command("adduser") & filters.private)
        async def adduser_handler(client: Client, message: Message):
            await self._handle_adduser(message)
        
        @self.app.on_message(filters.command("approve") & filters.private)
        async def approve_handler(client: Client, message: Message):
            await self._handle_approve(message)
        
        @self.app.on_message(filters.command("pending") & filters.private)
        async def pending_handler(client: Client, message: Message):
            await self._handle_pending(message)
        
        @self.app.on_message(filters.command("stats") & filters.private)
        async def stats_handler(client: Client, message: Message):
            await self._handle_stats(message)
        
        @self.app.on_message(filters.channel | filters.group)
        async def message_handler(client: Client, message: Message):
            await self._handle_reaction(message)
    
    async def _handle_start(self, message: Message):
        """Handle /start command"""
        try:
            wallpaper_url = await self._get_wallpaper()
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ Add to Channel", url=f"https://t.me/{self.app.me.username}?startchannel"),
                    InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{self.app.me.username}?startgroup"),
                ],
                [
                    InlineKeyboardButton("📚 Commands", callback_data="commands"),
                    InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/MrDhanpalSharma"),
                ],
                [
                    InlineKeyboardButton("👥 Community", url="https://t.me/THEUPDATEDGUYS"),
                ],
            ])
            
            caption = (
                "**🤖 Telegram Auto Reaction Bot**\n\n"
                "✨ Premium auto-reaction system for channels and groups\n"
                "🎯 Fully managed from web dashboard\n"
                "⚡ Real-time analytics and control\n\n"
                "**Features:**\n"
                "• Auto reactions with custom emojis\n"
                "• Smart delay and anti-flood protection\n"
                "• Live analytics dashboard\n"
                "• Multi-chat management\n\n"
                "**Developer:** [Mr. Dhanpal Sharma](https://t.me/MrDhanpalSharma)\n"
                "**Community:** [The Updated Guys](https://t.me/THEUPDATEDGUYS)\n\n"
                "_Powered by The Updated Guys 🌟_"
            )
            
            await message.reply_photo(
                photo=wallpaper_url,
                caption=caption,
                reply_markup=keyboard,
            )
        
        except Exception as e:
            logger.error(f"Start command error: {str(e)}")
            await message.reply_text("⚠️ An error occurred. Please try again.")
    
    async def _handle_adduser(self, message: Message):
        """Handle /adduser command"""
        if message.from_user.id != settings.OWNER_TELEGRAM_ID:
            await message.reply_text("❌ This command is owner-only.")
            return
        
        try:
            args = message.text.split(maxsplit=2)
            
            if len(args) != 3:
                await message.reply_text(
                    "**Usage:**\n"
                    "`/adduser username password`\n\n"
                    "**Example:**\n"
                    "`/adduser john SecurePass123`"
                )
                return
            
            username = args[1]
            password = args[2]
            
            result = await auth_manager.create_user(
                username=username,
                password=password,
                role="operator",
                status="approved",
            )
            
            await message.reply_text(
                f"✅ **User Created**\n\n"
                f"**Username:** `{username}`\n"
                f"**Role:** operator\n"
                f"**Status:** approved\n\n"
                f"User can now login to the dashboard."
            )
            
            logger.info(f"User created via Telegram: {username}")
        
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
            logger.error(f"Add user error: {str(e)}")
    
    async def _handle_approve(self, message: Message):
        """Handle /approve command"""
        if message.from_user.id != settings.OWNER_TELEGRAM_ID:
            await message.reply_text("❌ This command is owner-only.")
            return
        
        try:
            args = message.text.split()
            
            if len(args) != 2:
                await message.reply_text(
                    "**Usage:**\n"
                    "`/approve username`\n\n"
                    "**Example:**\n"
                    "`/approve john`"
                )
                return
            
            username = args[1]
            
            success = await auth_manager.approve_user(username)
            
            if success:
                await message.reply_text(f"✅ User **{username}** has been approved!")
            else:
                await message.reply_text(f"❌ User **{username}** not found or already approved.")
        
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
            logger.error(f"Approve user error: {str(e)}")
    
    async def _handle_pending(self, message: Message):
        """Handle /pending command"""
        if message.from_user.id != settings.OWNER_TELEGRAM_ID:
            await message.reply_text("❌ This command is owner-only.")
            return
        
        try:
            pending_users = await auth_manager.get_pending_users()
            
            if not pending_users:
                await message.reply_text("✅ No pending users.")
                return
            
            text = "**📋 Pending Users:**\n\n"
            
            for user in pending_users:
                text += f"• **{user['username']}**\n"
                text += f"  Created: {user['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                if user.get('telegram_id'):
                    text += f"  Telegram ID: `{user['telegram_id']}`\n"
                text += f"  Approve: `/approve {user['username']}`\n\n"
            
            await message.reply_text(text)
        
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
            logger.error(f"Pending users error: {str(e)}")
    
    async def _handle_stats(self, message: Message):
        """Handle /stats command"""
        try:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
            uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m"
            
            text = (
                f"**📊 Bot Statistics**\n\n"
                f"**Uptime:** {uptime_str}\n"
                f"**Total Reactions:** {self.stats['total_reactions']}\n"
                f"**Active Chats:** {len(self.stats['active_chats'])}\n"
                f"**Flood Waits:** {self.stats['flood_waits']}\n"
                f"**Errors:** {self.stats['errors']}\n\n"
                f"_View detailed analytics on the dashboard_"
            )
            
            await message.reply_text(text)
        
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
            logger.error(f"Stats command error: {str(e)}")
    
    async def _handle_reaction(self, message: Message):
        """Handle automatic reactions"""
        try:
            chat_config = await db.get_collection("chats").find_one({"chat_id": message.chat.id})
            
            if not chat_config or not chat_config.get("enabled", True):
                return
            
            settings_doc = await db.get_collection("settings").find_one({"key": "bot_settings"})
            if settings_doc and not settings_doc.get("value", {}).get("auto_react", True):
                return
            
            if not chat_config.get("react_to_text", True) and message.text:
                return
            
            if not chat_config.get("react_to_media", True) and (message.photo or message.video or message.document):
                return
            
            if not chat_config.get("react_to_forwards", False) and message.forward_date:
                return
            
            delay_min = chat_config.get("delay_min", 1)
            delay_max = chat_config.get("delay_max", 5)
            await asyncio.sleep(random.uniform(delay_min, delay_max))
            
            emoji = await self._select_emoji(chat_config)
            
            await self._send_reaction(message, emoji, chat_config)
        
        except Exception as e:
            logger.error(f"Reaction handler error: {str(e)}")
            self.stats["errors"] += 1
    
    async def _select_emoji(self, chat_config: Dict[str, Any]) -> str:
        """Select emoji based on configuration"""
        mode = chat_config.get("reaction_mode", "random")
        emojis = chat_config.get("emojis", ["❤️", "🔥", "👍"])
        
        if mode == "random":
            return random.choice(emojis)
        elif mode == "fixed":
            return emojis[0] if emojis else "❤️"
        elif mode == "sequential":
            last_emoji_idx = chat_config.get("last_emoji_idx", 0)
            emoji = emojis[last_emoji_idx % len(emojis)]
            
            await db.get_collection("chats").update_one(
                {"chat_id": chat_config["chat_id"]},
                {"$set": {"last_emoji_idx": (last_emoji_idx + 1) % len(emojis)}}
            )
            
            return emoji
        
        return "❤️"
    
    async def _send_reaction(
        self,
        message: Message,
        emoji: str,
        chat_config: Dict[str, Any],
        attempt: int = 0,
    ):
        """Send reaction with retry logic"""
        max_retries = 3
        
        try:
            await self.app.send_reaction(
                chat_id=message.chat.id,
                message_id=message.id,
                emoji=emoji,
            )
            
            self.stats["total_reactions"] += 1
            self.stats["active_chats"].add(message.chat.id)
            
            await db.get_collection("reactions").insert_one({
                "chat_id": message.chat.id,
                "message_id": message.id,
                "emoji": emoji,
                "timestamp": datetime.utcnow(),
                "status": "success",
                "retry_count": attempt,
            })
            
            await self._update_analytics("reaction_sent", 1, {"emoji": emoji})
        
        except FloodWait as e:
            self.stats["flood_waits"] += 1
            wait_time = e.value
            
            logger.warning(f"FloodWait: {wait_time}s for chat {message.chat.id}")
            
            await db.get_collection("reactions").insert_one({
                "chat_id": message.chat.id,
                "message_id": message.id,
                "emoji": emoji,
                "timestamp": datetime.utcnow(),
                "status": "flood_wait",
                "error": f"FloodWait {wait_time}s",
                "retry_count": attempt,
            })
            
            if attempt < max_retries:
                await asyncio.sleep(wait_time * 1.5)
                await self._send_reaction(message, emoji, chat_config, attempt + 1)
        
        except RPCError as e:
            self.stats["errors"] += 1
            
            logger.error(f"RPC Error: {str(e)} for chat {message.chat.id}")
            
            await db.get_collection("reactions").insert_one({
                "chat_id": message.chat.id,
                "message_id": message.id,
                "emoji": emoji,
                "timestamp": datetime.utcnow(),
                "status": "error",
                "error": str(e),
                "retry_count": attempt,
            })
            
            if attempt < max_retries and "FLOOD" not in str(e).upper():
                delay = exponential_backoff(attempt)
                await asyncio.sleep(delay)
                await self._send_reaction(message, emoji, chat_config, attempt + 1)
        
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Unexpected error in send_reaction: {str(e)}")
    
    async def _get_wallpaper(self) -> str:
        """Get wallpaper from MongoDB cache or API"""
        try:
            import httpx
            
            cache_key = "wallpaper_current"
            cached = await db.get_collection("cache").find_one({"key": cache_key})
            
            if cached and cached.get("expires_at") > datetime.utcnow():
                return cached["value"]
            
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(settings.WALLPAPER_API_PRIMARY, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    url = data["results"][0]["url"]
                except Exception:
                    response = await client.get(settings.WALLPAPER_API_FALLBACK, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    url = data["url"]
                
                await db.get_collection("cache").update_one(
                    {"key": cache_key},
                    {
                        "$set": {
                            "value": url,
                            "expires_at": datetime.utcnow() + timedelta(seconds=settings.WALLPAPER_CACHE_TTL),
                            "updated_at": datetime.utcnow(),
                        }
                    },
                    upsert=True
                )
                
                return url
        
        except Exception as e:
            logger.error(f"Wallpaper fetch error: {str(e)}")
            return "https://i.imgur.com/rYZ5GbL.jpg"
    
    async def _update_analytics(self, metric_type: str, value: float, metadata: Optional[Dict] = None):
        """Update analytics data"""
        try:
            now = datetime.utcnow()
            
            await db.get_collection("analytics").insert_one({
                "metric_type": metric_type,
                "value": value,
                "timestamp": now,
                "date": now.strftime("%Y-%m-%d"),
                "hour": now.hour,
                "metadata": metadata or {},
            })
        except Exception as e:
            logger.error(f"Analytics update error: {str(e)}")
    
    def get_uptime(self) -> int:
        """Get bot uptime in seconds"""
        return int((datetime.utcnow() - self.start_time).total_seconds())


telegram_bot = TelegramBot()
