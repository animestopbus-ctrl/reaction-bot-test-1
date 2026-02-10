import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from LastPerson07.config import settings
from LastPerson07.database import db
from LastPerson07.logger import logger
from LastPerson07.auth import auth_manager
from LastPerson07.reactions import telegram_bot
from LastPerson07.websocket import websocket_manager
from LastPerson07.analytics import analytics_engine
from LastPerson07.admin import admin_manager
from LastPerson07.models import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    ChatConfig,
    StatsResponse,
    HealthResponse,
    WallpaperResponse,
)
from LastPerson07.utils import (
    verify_password,
    create_access_token,
    create_refresh_token,
    sanitize_input,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting Telegram Reaction SaaS...")
    
    await db.connect()
    logger.info("✅ Database connected")
    
    await auth_manager.initialize()
    logger.info("✅ Auth manager initialized")
    
    await websocket_manager.initialize()
    logger.info("✅ WebSocket manager initialized")
    
    asyncio.create_task(telegram_bot.initialize())
    logger.info("✅ Telegram bot initialized")
    
    yield
    
    logger.info("🛑 Shutting down Telegram Reaction SaaS...")
    
    await telegram_bot.stop()
    await websocket_manager.close()
    await auth_manager.close()
    await db.disconnect()
    
    logger.info("✅ Shutdown complete")


app = FastAPI(
    title="Telegram Reaction SaaS",
    description="Production-grade Telegram auto-reaction platform",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    health = await admin_manager.get_system_health()
    return health


@app.post(f"{settings.API_PREFIX}/auth/register", response_model=UserResponse)
async def register(user: UserCreate):
    """Register a new user (approval required)"""
    try:
        username = sanitize_input(user.username, max_length=50)
        
        result = await auth_manager.create_user(
            username=username,
            password=user.password,
            telegram_id=user.telegram_id,
            role=user.role,
            status="pending",
        )
        
        return UserResponse(
            id=result["id"],
            username=result["username"],
            email=user.email,
            telegram_id=user.telegram_id,
            role=result["role"],
            status=result["status"],
            created_at=datetime.utcnow(),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@app.post(f"{settings.API_PREFIX}/auth/login", response_model=TokenResponse)
async def login(request: Request, login_data: LoginRequest):
    """Login and get access tokens"""
    await auth_manager.check_rate_limit(request, "login", 5, 300)
    
    username = sanitize_input(login_data.username, max_length=50)
    
    user_data = await db.get_collection("users").find_one({"username": username})
    
    if not user_data or not verify_password(login_data.password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if user_data["status"] != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending approval"
        )
    
    access_token = create_access_token({"sub": username, "role": user_data["role"]})
    refresh_token = create_refresh_token({"sub": username})
    
    await auth_manager.update_last_login(username)
    
    logger.info(f"User logged in: {username}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@app.get(f"{settings.API_PREFIX}/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(auth_manager.get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        telegram_id=current_user.telegram_id,
        role=current_user.role,
        status=current_user.status,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@app.get(f"{settings.API_PREFIX}/users")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(auth_manager.get_current_user)
):
    """Get all users (admin/owner only)"""
    return await admin_manager.get_all_users(skip, limit, current_user)


@app.post(f"{settings.API_PREFIX}/users/{{username}}/approve")
async def approve_user(
    username: str,
    current_user = Depends(auth_manager.get_current_user)
):
    """Approve pending user (owner only)"""
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can approve users"
        )
    
    success = await auth_manager.approve_user(username)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or already approved"
        )
    
    return {"username": username, "approved": True}


@app.put(f"{settings.API_PREFIX}/users/{{username}}/role")
async def update_user_role(
    username: str,
    new_role: str,
    current_user = Depends(auth_manager.get_current_user)
):
    """Update user role (owner only)"""
    return await admin_manager.update_user_role(username, new_role, current_user)


@app.delete(f"{settings.API_PREFIX}/users/{{username}}")
async def delete_user(
    username: str,
    current_user = Depends(auth_manager.get_current_user)
):
    """Delete user (owner only)"""
    return await admin_manager.delete_user(username, current_user)


@app.get(f"{settings.API_PREFIX}/chats")
async def get_chats(current_user = Depends(auth_manager.get_current_user)):
    """Get all configured chats"""
    return await admin_manager.get_all_chats(current_user)


@app.post(f"{settings.API_PREFIX}/chats")
async def add_chat(
    chat_config: ChatConfig,
    current_user = Depends(auth_manager.get_current_user)
):
    """Add or update chat configuration"""
    return await admin_manager.add_chat(chat_config, current_user)


@app.put(f"{settings.API_PREFIX}/chats/{{chat_id}}")
async def update_chat(
    chat_id: int,
    updates: dict,
    current_user = Depends(auth_manager.get_current_user)
):
    """Update chat configuration"""
    return await admin_manager.update_chat(chat_id, updates, current_user)


@app.delete(f"{settings.API_PREFIX}/chats/{{chat_id}}")
async def delete_chat(
    chat_id: int,
    current_user = Depends(auth_manager.get_current_user)
):
    """Delete chat configuration"""
    return await admin_manager.delete_chat(chat_id, current_user)


@app.get(f"{settings.API_PREFIX}/stats", response_model=StatsResponse)
async def get_stats(current_user = Depends(auth_manager.get_current_user)):
    """Get comprehensive statistics"""
    total_reactions = await analytics_engine.get_total_reactions()
    reactions_per_second = await analytics_engine.get_reactions_per_second(hours=1)
    active_chats = await analytics_engine.get_active_chats()
    flood_waits = await analytics_engine.get_flood_waits(hours=24)
    error_rate = await analytics_engine.get_error_rate(hours=24)
    emoji_usage = await analytics_engine.get_emoji_usage(hours=24)
    hourly_stats = await analytics_engine.get_hourly_stats(hours=24)
    
    bot_uptime = telegram_bot.get_uptime() if telegram_bot.is_running else 0
    
    return StatsResponse(
        total_reactions=total_reactions,
        reactions_per_second=reactions_per_second,
        active_chats=active_chats,
        bot_uptime=bot_uptime,
        flood_waits=flood_waits,
        error_rate=error_rate,
        emoji_usage=emoji_usage,
        hourly_stats=hourly_stats,
    )


@app.get(f"{settings.API_PREFIX}/stats/chat/{{chat_id}}")
async def get_chat_stats(
    chat_id: int,
    days: int = 7,
    current_user = Depends(auth_manager.get_current_user)
):
    """Get statistics for a specific chat"""
    return await analytics_engine.get_chat_stats(chat_id, days)


@app.get(f"{settings.API_PREFIX}/stats/daily")
async def get_daily_summary(current_user = Depends(auth_manager.get_current_user)):
    """Get daily summary statistics"""
    return await analytics_engine.get_daily_summary()


@app.get(f"{settings.API_PREFIX}/stats/top-chats")
async def get_top_chats(
    limit: int = 10,
    days: int = 7,
    current_user = Depends(auth_manager.get_current_user)
):
    """Get top performing chats"""
    return await analytics_engine.get_top_chats(limit, days)


@app.get(f"{settings.API_PREFIX}/settings/bot")
async def get_bot_settings(current_user = Depends(auth_manager.get_current_user)):
    """Get bot settings"""
    return await admin_manager.get_bot_settings(current_user)


@app.put(f"{settings.API_PREFIX}/settings/bot")
async def update_bot_settings(
    settings_data: dict,
    current_user = Depends(auth_manager.get_current_user)
):
    """Update bot settings"""
    return await admin_manager.update_bot_settings(settings_data, current_user)


@app.get(f"{settings.API_PREFIX}/wallpaper", response_model=WallpaperResponse)
async def get_wallpaper(request: Request):
    """Get cached or fresh wallpaper"""
    await auth_manager.check_rate_limit(request, "wallpaper", 10, 60)
    
    try:
        cache_key = "wallpaper_current"
        cached = await db.get_collection("cache").find_one({"key": cache_key})
        
        if cached and cached.get("expires_at") > datetime.utcnow():
            return WallpaperResponse(url=cached["value"], cached=True, source="cache")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(settings.WALLPAPER_API_PRIMARY, timeout=10)
                response.raise_for_status()
                data = response.json()
                url = data["results"][0]["url"]
                source = "primary"
            except Exception:
                response = await client.get(settings.WALLPAPER_API_FALLBACK, timeout=10)
                response.raise_for_status()
                data = response.json()
                url = data["url"]
                source = "fallback"
            
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
            
            return WallpaperResponse(url=url, cached=False, source=source)
    
    except Exception as e:
        logger.error(f"Wallpaper fetch error: {str(e)}")
        return WallpaperResponse(
            url="https://i.imgur.com/rYZ5GbL.jpg",
            cached=False,
            source="fallback"
        )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"WebSocket message received: {data}")
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        websocket_manager.disconnect(websocket)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1,
    )
