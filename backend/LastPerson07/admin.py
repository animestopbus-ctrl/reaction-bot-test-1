from datetime import datetime
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from LastPerson07.database import db
from LastPerson07.auth import auth_manager
from LastPerson07.models import UserInDB, ChatConfig
from LastPerson07.logger import logger
from LastPerson07.websocket import websocket_manager


class AdminManager:
    """Production-grade admin management"""
    
    @staticmethod
    async def get_all_users(
        skip: int = 0,
        limit: int = 100,
        current_user: UserInDB = Depends(auth_manager.get_current_user)
    ) -> List[dict]:
        """Get all users (admin/owner only)"""
        if current_user.role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        cursor = db.get_collection("users").find().skip(skip).limit(limit)
        users = []
        
        async for user in cursor:
            users.append({
                "id": str(user["_id"]),
                "username": user["username"],
                "email": user.get("email"),
                "telegram_id": user.get("telegram_id"),
                "role": user["role"],
                "status": user["status"],
                "created_at": user["created_at"],
                "last_login": user.get("last_login"),
            })
        
        return users
    
    @staticmethod
    async def update_user_role(
        username: str,
        new_role: str,
        current_user: UserInDB = Depends(auth_manager.get_current_user)
    ) -> dict:
        """Update user role (owner only)"""
        if current_user.role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner can change user roles"
            )
        
        valid_roles = ["owner", "admin", "operator", "viewer"]
        if new_role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        
        result = await db.get_collection("users").update_one(
            {"username": username},
            {"$set": {"role": new_role, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User role updated: {username} -> {new_role} by {current_user.username}")
        
        return {"username": username, "new_role": new_role, "success": True}
    
    @staticmethod
    async def delete_user(
        username: str,
        current_user: UserInDB = Depends(auth_manager.get_current_user)
    ) -> dict:
        """Delete user (owner only)"""
        if current_user.role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner can delete users"
            )
        
        if username == current_user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete yourself"
            )
        
        result = await db.get_collection("users").delete_one({"username": username})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User deleted: {username} by {current_user.username}")
        
        return {"username": username, "deleted": True}
    
    @staticmethod
    async def get_all_chats(
        current_user: UserInDB = Depends(auth_manager.get_current_user)
    ) -> List[dict]:
        """Get all configured chats"""
        if current_user.role not in ["owner", "admin", "operator"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        cursor = db.get_collection("chats").find().sort("added_at", -1)
        chats = []
        
        async for chat in cursor:
            chats.append({
                "chat_id": chat["chat_id"],
                "chat_title": chat["chat_title"],
                "chat_type": chat["chat_type"],
                "enabled": chat.get("enabled", True),
                "reaction_mode": chat.get("reaction_mode", "random"),
                "emojis": chat.get("emojis", []),
                "delay_min": chat.get("delay_min", 1),
                "delay_max": chat.get("delay_max", 5),
                "react_to_media": chat.get("react_to_media", True),
                "react_to_text": chat.get("react_to_text", True),
                "react_to_forwards": chat.get("react_to_forwards", False),
                "added_at": chat["added_at"],
                "added_by": chat.get("added_by", "unknown"),
            })
        
        return chats
    
    @staticmethod
    async def add_chat(
        chat_config: ChatConfig,
        current_user: UserInDB = Depends(auth_manager.get_current_user)
    ) -> dict:
        """Add or update chat configuration"""
        if current_user.role not in ["owner", "admin", "operator"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        chat_data = chat_config.dict()
        chat_data["added_by"] = current_user.username
        chat_data["updated_at"] = datetime.utcnow()
        
        result = await db.get_collection("chats").update_one(
            {"chat_id": chat_config.chat_id},
            {"$set": chat_data},
            upsert=True
        )
        
        logger.info(f"Chat configured: {chat_config.chat_id} ({chat_config.chat_title}) by {current_user.username}")
        
        await websocket_manager.notify_chat_added(
            chat_config.chat_id,
            chat_config.chat_title
        )
        
        return {
            "chat_id": chat_config.chat_id,
            "success": True,
            "is_new": result.upserted_id is not None
        }
    
    @staticmethod
    async def update_chat(
        chat_id: int,
        updates: dict,
        current_user: UserInDB = Depends(auth_manager.get_current_user)
    ) -> dict:
        """Update chat configuration"""
        if current_user.role not in ["owner", "admin", "operator"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        updates["updated_at"] = datetime.utcnow()
        
        result = await db.get_collection("chats").update_one(
            {"chat_id": chat_id},
            {"$set": updates}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        logger.info(f"Chat updated: {chat_id} by {current_user.username}")
        
        await websocket_manager.notify_chat_updated(chat_id, updates)
        
        return {"chat_id": chat_id, "success": True}
    
    @staticmethod
    async def delete_chat(
        chat_id: int,
        current_user: UserInDB = Depends(auth_manager.get_current_user)
    ) -> dict:
        """Delete chat configuration"""
        if current_user.role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        result = await db.get_collection("chats").delete_one({"chat_id": chat_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        logger.info(f"Chat deleted: {chat_id} by {current_user.username}")
        
        return {"chat_id": chat_id, "deleted": True}
    
    @staticmethod
    async def get_bot_settings(
        current_user: UserInDB = Depends(auth_manager.get_current_user)
    ) -> dict:
        """Get bot settings"""
        settings_doc = await db.get_collection("settings").find_one({"key": "bot_settings"})
        
        if not settings_doc:
            default_settings = {
                "auto_react": True,
                "default_emojis": ["❤️", "🔥", "👍", "😍", "✨"],
                "default_delay_min": 1,
                "default_delay_max": 5,
                "max_retries": 3,
                "retry_delay": 60,
                "flood_wait_multiplier": 1.5,
                "enable_sentiment": False,
            }
            
            await db.get_collection("settings").insert_one({
                "key": "bot_settings",
                "value": default_settings,
                "updated_at": datetime.utcnow(),
            })
            
            return default_settings
        
        return settings_doc.get("value", {})
    
    @staticmethod
    async def update_bot_settings(
        settings: dict,
        current_user: UserInDB = Depends(auth_manager.get_current_user)
    ) -> dict:
        """Update bot settings"""
        if current_user.role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        await db.get_collection("settings").update_one(
            {"key": "bot_settings"},
            {
                "$set": {
                    "value": settings,
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True
        )
        
        logger.info(f"Bot settings updated by {current_user.username}")
        
        return {"success": True, "settings": settings}
    
    @staticmethod
    async def get_system_health() -> dict:
        """Get system health status"""
        try:
            mongodb_healthy = True
            try:
                await db.client.admin.command('ping')
            except:
                mongodb_healthy = False
            
            from LastPerson07.reactions import telegram_bot
            telegram_healthy = telegram_bot.is_running
            
            bot_uptime = telegram_bot.get_uptime() if telegram_bot.is_running else 0
            
            return {
                "status": "healthy" if (mongodb_healthy and telegram_healthy) else "degraded",
                "timestamp": datetime.utcnow(),
                "mongodb": mongodb_healthy,
                "redis": True,
                "telegram": telegram_healthy,
                "uptime": bot_uptime,
            }
        
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow(),
                "mongodb": False,
                "redis": False,
                "telegram": False,
                "uptime": 0,
                "error": str(e),
            }


admin_manager = AdminManager()
