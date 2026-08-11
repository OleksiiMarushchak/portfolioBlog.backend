import asyncio
from functools import partial
import bcrypt

import jwt
import uuid
from datetime import datetime, timedelta
from config import settings

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10)).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

async def verify_password_async(password: str, hashed: str) -> bool:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        partial(bcrypt.checkpw, password.encode(), hashed.encode())
    )


def create_access_token(user_id: int, session_id: int):
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "exp": datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        "iat": datetime.utcnow(),
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def create_refresh_token(session_id: int):
    payload = {
        "sid": str(session_id),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        ),
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

from jwt import ExpiredSignatureError, InvalidTokenError

def decode_token(token: str):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except ExpiredSignatureError:
        return {"error": "expired"}
    except InvalidTokenError:
        return {"error": "invalid"}
