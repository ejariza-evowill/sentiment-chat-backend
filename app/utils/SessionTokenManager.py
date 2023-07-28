import jwt

from datetime import datetime, timedelta, timezone

from app.config import ( 
    ACCESS_TOKEN_SECRET, REFRESH_TOKEN_SECRET, 
    ACCESS_TOKEN_EXPIRE, REFRESH_TOKEN_EXPIRE 
    )

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE)
    to_encode.update({"exp": expire})
    return (jwt.encode(to_encode, ACCESS_TOKEN_SECRET, algorithm="HS256"), expire)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=REFRESH_TOKEN_EXPIRE)
    to_encode.update({"exp": expire})
    return (jwt.encode(data, REFRESH_TOKEN_SECRET, algorithm="HS256"), expire)

def get_payload_from_token(token: str, secret: str = ACCESS_TOKEN_SECRET):
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Signature has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
