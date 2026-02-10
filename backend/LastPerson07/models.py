from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class UserBase(BaseModel):
    """Base user model"""
    username: str
    email: Optional[str] = None
    telegram_id: Optional[int] = None
    role: str = "viewer"
    status: str = "pending"


class UserCreate(UserBase):
    """User creation model"""
    password: str


class UserInDB(UserBase):
    """User database model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UserResponse(BaseModel):
    """User response model"""
    id: str
    username: str
    email: Optional[str] = None
    telegram_id: Optional[int] = None
    role: str
    status: str
    created_at: datetime
    last_login: Optional[datetime] = None


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class ChatConfig(BaseModel):
    """Chat configuration model"""
    chat_id: int
    chat_title: str
    chat_type: str
    enabled: bool = True
    reaction_mode: str = "random"
    emojis: List[str] = ["❤️", "🔥", "👍"]
    delay_min: int = 1
    delay_max: int = 5
    react_to_media: bool = True
    react_to_text: bool = True
    react_to_forwards: bool = False
    added_at: datetime = Field(default_factory=datetime.utcnow)
    added_by: str


class ReactionRecord(BaseModel):
    """Reaction record model"""
    chat_id: int
    message_id: int
    emoji: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    status: str = "success"
    error: Optional[str] = None
    retry_count: int = 0


class AnalyticsRecord(BaseModel):
    """Analytics record model"""
    metric_type: str
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    date: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))
    hour: int = Field(default_factory=lambda: datetime.utcnow().hour)
    metadata: Optional[Dict[str, Any]] = None


class BotSettings(BaseModel):
    """Bot settings model"""
    auto_react: bool = True
    default_emojis: List[str] = ["❤️", "🔥", "👍", "😍", "✨"]
    default_delay_min: int = 1
    default_delay_max: int = 5
    max_retries: int = 3
    retry_delay: int = 60
    flood_wait_multiplier: float = 1.5
    enable_sentiment: bool = False
    log_channel_id: Optional[int] = None


class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StatsResponse(BaseModel):
    """Statistics response model"""
    total_reactions: int
    reactions_per_second: float
    active_chats: int
    bot_uptime: int
    flood_waits: int
    error_rate: float
    emoji_usage: Dict[str, int]
    hourly_stats: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    mongodb: bool
    redis: bool
    telegram: bool
    uptime: int


class WallpaperResponse(BaseModel):
    """Wallpaper API response model"""
    url: str
    cached: bool = False
    source: str = "primary"
