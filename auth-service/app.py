"""Minimal FastAPI Auth Service - JWT token issuing and verification"""
import os
import logging
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import jwt

# Logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

app = FastAPI(title="Auth Service", version="0.1.0")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRY_MINUTES = int(os.getenv("TOKEN_EXPIRY_MINUTES", "15"))

# User Service URL for verification
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8080")

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenVerifyRequest(BaseModel):
    token: str

class TokenVerifyResponse(BaseModel):
    valid: bool
    username: str = None
    user_id: int = None

@app.get("/healthz")
async def liveness():
    """Liveness probe - always returns 200 if service is running"""
    return {"status": "alive"}

@app.get("/ready")
async def readiness():
    """Readiness probe"""
    return {"status": "ready"}

@app.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint"""
    return {"service": "auth-service", "version": "0.1.0"}

@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login endpoint: issues a JWT token.
    In a real scenario, you'd verify username/password against the User Service.
    For now, we accept any username/password and issue a token.
    """
    try:
        logger.info(f"Login attempt for user: {request.username}")
        
        # TODO: Call User Service to verify user credentials
        # For now, we just issue a token for demo purposes
        
        # Create JWT payload
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
        
        payload = {
            "sub": request.username,
            "iat": now,
            "exp": expires_at,
            "user_id": 1  # In production, get from User Service
        }
        
        # Encode JWT
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        logger.info(f"✓ Token issued for user: {request.username}")
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=TOKEN_EXPIRY_MINUTES * 60
        )
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/verify", response_model=TokenVerifyResponse)
async def verify_token(request: TokenVerifyRequest):
    """
    Verify JWT token.
    Other services call this to check if a token is valid.
    """
    try:
        # Decode and verify JWT
        payload = jwt.decode(request.token, SECRET_KEY, algorithms=[ALGORITHM])
        
        username = payload.get("sub")
        user_id = payload.get("user_id")
        
        logger.info(f"✓ Token verified for user: {username}")
        return TokenVerifyResponse(
            valid=True,
            username=username,
            user_id=user_id
        )
    except jwt.ExpiredSignatureError:
        logger.warning("Token verification failed: token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/keys")
async def get_public_keys():
    """
    Return public key (JWKS format) for token verification.
    Other services can use this to verify tokens locally without calling /verify.
    For now, we return a simple representation.
    """
    return {
        "keys": [
            {
                "kty": "oct",
                "kid": "default",
                "alg": ALGORITHM,
                "use": "sig"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Auth Service starting on port {port}")
    logger.info(f"User Service URL: {USER_SERVICE_URL}")
    uvicorn.run(app, host="0.0.0.0", port=port)
