from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from LastPerson07.database import db
from LastPerson07.logger import logger


class AnalyticsEngine:
    """Production-grade analytics engine"""
    
    @staticmethod
    async def get_total_reactions() -> int:
        """Get total reactions count"""
        try:
            count = await db.get_collection("reactions").count_documents({"status": "success"})
            return count
        except Exception as e:
            logger.error(f"Analytics error (total_reactions): {str(e)}")
            return 0
    
    @staticmethod
    async def get_reactions_per_second(hours: int = 1) -> float:
        """Calculate reactions per second"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            count = await db.get_collection("reactions").count_documents({
                "status": "success",
                "timestamp": {"$gte": start_time}
            })
            
            seconds = hours * 3600
            return round(count / seconds, 2) if seconds > 0 else 0.0
        except Exception as e:
            logger.error(f"Analytics error (reactions_per_second): {str(e)}")
            return 0.0
    
    @staticmethod
    async def get_active_chats() -> int:
        """Get count of active chats"""
        try:
            count = await db.get_collection("chats").count_documents({"enabled": True})
            return count
        except Exception as e:
            logger.error(f"Analytics error (active_chats): {str(e)}")
            return 0
    
    @staticmethod
    async def get_flood_waits(hours: int = 24) -> int:
        """Get flood wait count"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            count = await db.get_collection("reactions").count_documents({
                "status": "flood_wait",
                "timestamp": {"$gte": start_time}
            })
            
            return count
        except Exception as e:
            logger.error(f"Analytics error (flood_waits): {str(e)}")
            return 0
    
    @staticmethod
    async def get_error_rate(hours: int = 24) -> float:
        """Calculate error rate percentage"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            total = await db.get_collection("reactions").count_documents({
                "timestamp": {"$gte": start_time}
            })
            
            errors = await db.get_collection("reactions").count_documents({
                "status": {"$in": ["error", "flood_wait"]},
                "timestamp": {"$gte": start_time}
            })
            
            return round((errors / total * 100), 2) if total > 0 else 0.0
        except Exception as e:
            logger.error(f"Analytics error (error_rate): {str(e)}")
            return 0.0
    
    @staticmethod
    async def get_emoji_usage(hours: int = 24) -> Dict[str, int]:
        """Get emoji usage statistics"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            pipeline = [
                {
                    "$match": {
                        "status": "success",
                        "timestamp": {"$gte": start_time}
                    }
                },
                {
                    "$group": {
                        "_id": "$emoji",
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"count": -1}
                },
                {
                    "$limit": 20
                }
            ]
            
            cursor = db.get_collection("reactions").aggregate(pipeline)
            result = {}
            
            async for doc in cursor:
                result[doc["_id"]] = doc["count"]
            
            return result
        except Exception as e:
            logger.error(f"Analytics error (emoji_usage): {str(e)}")
            return {}
    
    @staticmethod
    async def get_hourly_stats(hours: int = 24) -> List[Dict[str, Any]]:
        """Get hourly reaction statistics"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            pipeline = [
                {
                    "$match": {
                        "status": "success",
                        "timestamp": {"$gte": start_time}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$timestamp"},
                            "month": {"$month": "$timestamp"},
                            "day": {"$dayOfMonth": "$timestamp"},
                            "hour": {"$hour": "$timestamp"}
                        },
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]
            
            cursor = db.get_collection("reactions").aggregate(pipeline)
            result = []
            
            async for doc in cursor:
                date_info = doc["_id"]
                timestamp = datetime(
                    year=date_info["year"],
                    month=date_info["month"],
                    day=date_info["day"],
                    hour=date_info["hour"]
                )
                
                result.append({
                    "timestamp": timestamp.isoformat(),
                    "hour": date_info["hour"],
                    "count": doc["count"]
                })
            
            return result
        except Exception as e:
            logger.error(f"Analytics error (hourly_stats): {str(e)}")
            return []
    
    @staticmethod
    async def get_chat_stats(chat_id: int, days: int = 7) -> Dict[str, Any]:
        """Get statistics for a specific chat"""
        try:
            start_time = datetime.utcnow() - timedelta(days=days)
            
            total_reactions = await db.get_collection("reactions").count_documents({
                "chat_id": chat_id,
                "status": "success",
                "timestamp": {"$gte": start_time}
            })
            
            errors = await db.get_collection("reactions").count_documents({
                "chat_id": chat_id,
                "status": {"$in": ["error", "flood_wait"]},
                "timestamp": {"$gte": start_time}
            })
            
            pipeline = [
                {
                    "$match": {
                        "chat_id": chat_id,
                        "status": "success",
                        "timestamp": {"$gte": start_time}
                    }
                },
                {
                    "$group": {
                        "_id": "$emoji",
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"count": -1}
                },
                {
                    "$limit": 10
                }
            ]
            
            cursor = db.get_collection("reactions").aggregate(pipeline)
            emoji_usage = {}
            
            async for doc in cursor:
                emoji_usage[doc["_id"]] = doc["count"]
            
            return {
                "chat_id": chat_id,
                "total_reactions": total_reactions,
                "errors": errors,
                "error_rate": round((errors / (total_reactions + errors) * 100), 2) if (total_reactions + errors) > 0 else 0.0,
                "emoji_usage": emoji_usage,
            }
        except Exception as e:
            logger.error(f"Analytics error (chat_stats): {str(e)}")
            return {
                "chat_id": chat_id,
                "total_reactions": 0,
                "errors": 0,
                "error_rate": 0.0,
                "emoji_usage": {},
            }
    
    @staticmethod
    async def get_daily_summary(date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get daily summary statistics"""
        try:
            if date is None:
                date = datetime.utcnow()
            
            start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=1)
            
            total_reactions = await db.get_collection("reactions").count_documents({
                "status": "success",
                "timestamp": {"$gte": start_time, "$lt": end_time}
            })
            
            total_attempts = await db.get_collection("reactions").count_documents({
                "timestamp": {"$gte": start_time, "$lt": end_time}
            })
            
            errors = await db.get_collection("reactions").count_documents({
                "status": {"$in": ["error", "flood_wait"]},
                "timestamp": {"$gte": start_time, "$lt": end_time}
            })
            
            active_chats = await db.get_collection("reactions").distinct(
                "chat_id",
                {"timestamp": {"$gte": start_time, "$lt": end_time}}
            )
            
            return {
                "date": date.strftime("%Y-%m-%d"),
                "total_reactions": total_reactions,
                "total_attempts": total_attempts,
                "errors": errors,
                "success_rate": round((total_reactions / total_attempts * 100), 2) if total_attempts > 0 else 0.0,
                "active_chats": len(active_chats),
            }
        except Exception as e:
            logger.error(f"Analytics error (daily_summary): {str(e)}")
            return {
                "date": date.strftime("%Y-%m-%d") if date else "unknown",
                "total_reactions": 0,
                "total_attempts": 0,
                "errors": 0,
                "success_rate": 0.0,
                "active_chats": 0,
            }
    
    @staticmethod
    async def get_top_chats(limit: int = 10, days: int = 7) -> List[Dict[str, Any]]:
        """Get top performing chats"""
        try:
            start_time = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {
                    "$match": {
                        "status": "success",
                        "timestamp": {"$gte": start_time}
                    }
                },
                {
                    "$group": {
                        "_id": "$chat_id",
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"count": -1}
                },
                {
                    "$limit": limit
                }
            ]
            
            cursor = db.get_collection("reactions").aggregate(pipeline)
            result = []
            
            async for doc in cursor:
                chat_id = doc["_id"]
                
                chat_info = await db.get_collection("chats").find_one({"chat_id": chat_id})
                
                result.append({
                    "chat_id": chat_id,
                    "chat_title": chat_info.get("chat_title", "Unknown") if chat_info else "Unknown",
                    "reactions": doc["count"]
                })
            
            return result
        except Exception as e:
            logger.error(f"Analytics error (top_chats): {str(e)}")
            return []


analytics_engine = AnalyticsEngine()
