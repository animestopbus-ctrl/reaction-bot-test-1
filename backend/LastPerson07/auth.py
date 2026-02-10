import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from LastPerson07.config import settings
from LastPerson07.database import db
from LastPerson07.utils import decode_token, hash_password
from LastPerson07.models import UserInDB
from LastPerson07.logger import logger


security = HTTPBearer()


class AuthManager:
    """Production-grade authentication manager with MongoDB-based rate limiting"""
    
    def __init__(self):
        pass
    
    async def initialize(self):
        """Initialize auth manager"""
        logger.info("AuthManager: Initialized (MongoDB-only mode)")
    
    async def close(self):
        """Close auth manager"""
        logger.info("AuthManager: Closed")
    
    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> UserInDB:
        """Get current authenticated user"""
        token = credentials.credentials
        
        payload = decode_token(token)
        
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        
        user_data = await db.get_collection("users").find_one({"username": username})
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        user = UserInDB(**user_data)
        
        if user.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account pending approval",
            )
        
        return user
    
    async def require_role(self, required_roles: list[str]):
        """Dependency to check user role"""
        async def role_checker(user: UserInDB = Depends(self.get_current_user)):
            if user.role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )
            return user
        return role_checker
    
    async def check_rate_limit(
        self,
        request: Request,
        limit_type: str = "api",
        limit: int = 60,
        window: int = 60,
    ) -> bool:
        """
        Check rate limit using MongoDB sliding window
        
        Args:
            request: FastAPI request object
            limit_type: Type of rate limit (e.g., "login", "api")
            limit: Maximum number of requests
            window: Time window in seconds
        
        Returns:
            True if under limit, raises HTTPException if exceeded
        """
        client_ip = request.client.host
        key = f"{limit_type}:{client_ip}"
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(seconds=window)
        
        await db.get_collection("rate_limits").delete_many({
            "key": key,
            "timestamp": {"$lt": window_start}
        })
        
        count = await db.get_collection("rate_limits").count_documents({
            "key": key,
            "timestamp": {"$gte": window_start}
        })
        
        if count >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )
        
        await db.get_collection("rate_limits").insert_one({
            "key": key,
            "timestamp": current_time,
        })
        
        return True
    
    async def create_user(
        self,
        username: str,
        password: str,
        telegram_id: Optional[int] = None,
        role: str = "viewer",
        status: str = "pending",
    ) -> Dict[str, Any]:
        """Create a new user"""
        existing_user = await db.get_collection("users").find_one({"username": username})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )
        
        if telegram_id:
            existing_telegram = await db.get_collection("users").find_one({"telegram_id": telegram_id})
            if existing_telegram:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Telegram ID already linked",
                )
        
        hashed_password = hash_password(password)
        
        user_data = {
            "username": username,
            "hashed_password": hashed_password,
            "telegram_id": telegram_id,
            "role": role,
            "status": status,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        result = await db.get_collection("users").insert_one(user_data)
        
        logger.info(f"User created: {username} (role: {role}, status: {status})")
        
        return {
            "id": str(result.inserted_id),
            "username": username,
            "role": role,
            "status": status,
        }
    
    async def approve_user(self, username: str) -> bool:
        """Approve a pending user"""
        result = await db.get_collection("users").update_one(
            {"username": username, "status": "pending"},
            {"$set": {"status": "approved", "updated_at": datetime.utcnow()}},
        )
        
        if result.modified_count > 0:
            logger.info(f"User approved: {username}")
            return True
        
        return False
    
    async def update_last_login(self, username: str):
        """Update user's last login timestamp"""
        await db.get_collection("users").update_one(
            {"username": username},
            {"$set": {"last_login": datetime.utcnow()}},
        )
    
    async def get_pending_users(self) -> list[Dict[str, Any]]:
        """Get all pending users"""
        cursor = db.get_collection("users").find({"status": "pending"})
        users = []
        
        async for user in cursor:
            users.append({
                "id": str(user["_id"]),
                "username": user["username"],
                "telegram_id": user.get("telegram_id"),
                "created_at": user["created_at"],
            })
        
        return users


auth_manager = AuthManager()
