import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from LastPerson07.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def sanitize_input(text: str, max_length: int = 500) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not text:
        return ""
    
    text = text.strip()[:max_length]
    
    dangerous_chars = ["<", ">", "&", '"', "'", "/", "\\", "{", "}", ";"]
    for char in dangerous_chars:
        text = text.replace(char, "")
    
    return text


def validate_telegram_id(telegram_id: int) -> bool:
    """Validate Telegram user ID"""
    return isinstance(telegram_id, int) and telegram_id > 0


def validate_chat_id(chat_id: int) -> bool:
    """Validate Telegram chat ID"""
    return isinstance(chat_id, int) and chat_id != 0


def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"tk_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate exponential backoff delay"""
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = secrets.randbelow(1000) / 1000.0
    return delay + jitter


async def rate_limit_check(redis_client, key: str, limit: int, window: int) -> bool:
    """
    Check rate limit using sliding window algorithm
    
    Args:
        redis_client: Redis client instance
        key: Rate limit key (e.g., "login:user_id")
        limit: Maximum number of requests
        window: Time window in seconds
    
    Returns:
        True if under limit, False if exceeded
    """
    current_time = time.time()
    window_start = current_time - window
    
    pipe = redis_client.pipeline()
    
    pipe.zremrangebyscore(key, 0, window_start)
    
    pipe.zadd(key, {str(current_time): current_time})
    
    pipe.zcard(key)
    
    pipe.expire(key, window)
    
    results = await pipe.execute()
    
    request_count = results[2]
    
    return request_count <= limit


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable string"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def get_emoji_category(emoji: str) -> str:
    """Categorize emoji into groups"""
    emoji_categories = {
        "positive": ["❤️", "😍", "😊", "🥰", "😘", "🤗", "👍", "🔥", "✨", "💯", "🎉", "🌟"],
        "negative": ["😢", "😭", "😡", "😠", "💔", "👎", "😞", "😔", "🤬"],
        "neutral": ["👀", "🤔", "😐", "😑", "🙄"],
        "reactions": ["😂", "🤣", "😱", "😮", "🤯", "😎", "🤓", "🧐"],
    }
    
    for category, emojis in emoji_categories.items():
        if emoji in emojis:
            return category
    
    return "other"


def validate_emoji(emoji: str) -> bool:
    """Validate if string is a valid emoji"""
    import re
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    return bool(emoji_pattern.match(emoji))
