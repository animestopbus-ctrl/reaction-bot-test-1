import asyncio
import json
from datetime import datetime
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from LastPerson07.config import settings
from LastPerson07.logger import logger
from LastPerson07.analytics import analytics_engine
from LastPerson07.reactions import telegram_bot


class WebSocketManager:
    """Production-grade WebSocket manager with in-memory broadcasting"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.broadcast_task = None
    
    async def initialize(self):
        """Initialize WebSocket manager"""
        try:
            self.broadcast_task = asyncio.create_task(self._broadcast_stats_loop())
            
            logger.info("WebSocket manager initialized (MongoDB-only mode)")
        except Exception as e:
            logger.error(f"WebSocket manager initialization error: {str(e)}")
    
    async def close(self):
        """Close WebSocket manager"""
        try:
            if self.broadcast_task:
                self.broadcast_task.cancel()
            
            logger.info("WebSocket manager closed")
        except Exception as e:
            logger.error(f"WebSocket manager close error: {str(e)}")
    
    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
        
        await self._send_initial_data(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")
    
    async def _send_initial_data(self, websocket: WebSocket):
        """Send initial data to newly connected client"""
        try:
            stats = await self._get_current_stats()
            
            await websocket.send_json({
                "type": "initial_stats",
                "data": stats,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Error sending initial data: {str(e)}")
    
    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients"""
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {str(e)}")
                disconnected.add(connection)
        
        for connection in disconnected:
            self.disconnect(connection)
    
    async def _get_current_stats(self) -> Dict:
        """Get current statistics"""
        try:
            total_reactions = await analytics_engine.get_total_reactions()
            reactions_per_second = await analytics_engine.get_reactions_per_second(hours=1)
            active_chats = await analytics_engine.get_active_chats()
            flood_waits = await analytics_engine.get_flood_waits(hours=24)
            error_rate = await analytics_engine.get_error_rate(hours=24)
            emoji_usage = await analytics_engine.get_emoji_usage(hours=24)
            hourly_stats = await analytics_engine.get_hourly_stats(hours=24)
            
            bot_uptime = telegram_bot.get_uptime() if telegram_bot.is_running else 0
            
            return {
                "total_reactions": total_reactions,
                "reactions_per_second": reactions_per_second,
                "active_chats": active_chats,
                "bot_uptime": bot_uptime,
                "flood_waits": flood_waits,
                "error_rate": error_rate,
                "emoji_usage": emoji_usage,
                "hourly_stats": hourly_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting current stats: {str(e)}")
            return {
                "total_reactions": 0,
                "reactions_per_second": 0.0,
                "active_chats": 0,
                "bot_uptime": 0,
                "flood_waits": 0,
                "error_rate": 0.0,
                "emoji_usage": {},
                "hourly_stats": [],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _broadcast_stats_loop(self):
        """Broadcast stats every 5 seconds"""
        while True:
            try:
                await asyncio.sleep(5)
                
                if not self.active_connections:
                    continue
                
                stats = await self._get_current_stats()
                
                await self.broadcast({
                    "type": "stats_update",
                    "data": stats,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Stats broadcast loop error: {str(e)}")
    
    async def notify_reaction(self, chat_id: int, message_id: int, emoji: str, status: str):
        """Notify clients about a reaction event"""
        await self.broadcast({
            "type": "reaction",
            "data": {
                "chat_id": chat_id,
                "message_id": message_id,
                "emoji": emoji,
                "status": status,
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def notify_chat_added(self, chat_id: int, chat_title: str):
        """Notify clients about a new chat being added"""
        await self.broadcast({
            "type": "chat_added",
            "data": {
                "chat_id": chat_id,
                "chat_title": chat_title,
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def notify_chat_updated(self, chat_id: int, changes: Dict):
        """Notify clients about chat configuration changes"""
        await self.broadcast({
            "type": "chat_updated",
            "data": {
                "chat_id": chat_id,
                "changes": changes,
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def notify_error(self, error_type: str, message: str, details: Dict = None):
        """Notify clients about errors"""
        await self.broadcast({
            "type": "error",
            "data": {
                "error_type": error_type,
                "message": message,
                "details": details or {},
            },
            "timestamp": datetime.utcnow().isoformat()
        })


websocket_manager = WebSocketManager()
