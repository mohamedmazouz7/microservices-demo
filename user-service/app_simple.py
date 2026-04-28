"""Minimal FastAPI User Service with Postgres support and JWT authentication"""
import os
import logging
import json
import urllib.request
import urllib.error
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel

# Logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

app = FastAPI(title="User Service", version="0.2.0")

# Auth Service URL for token verification
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8080")

# Database connection (lazy-loaded)
db_connection = None

# In-memory user store (fallback if DB unavailable)
users_db = {
    1: {"id": 1, "username": "alice", "email": "alice@example.com"},
    2: {"id": 2, "username": "bob", "email": "bob@example.com"},
}

class User(BaseModel):
    id: int
    username: str
    email: str

def get_db_connection():
    """Lazy-load database connection using psycopg2"""
    global db_connection
    if db_connection is None:
        try:
            import psycopg2
            DATABASE_URL = os.getenv("DATABASE_URL")
            if not DATABASE_URL:
                logger.warning("DATABASE_URL not set, using in-memory storage")
                return None
            
            # Parse the URL and connect
            db_connection = psycopg2.connect(DATABASE_URL, connect_timeout=5)
            logger.info("✓ Database connection established")
        except ImportError:
            logger.warning("psycopg2 not installed, using in-memory storage")
            return None
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            return None
    return db_connection

def verify_token(authorization: str = Header(None)):
    """
    Verify JWT token by calling Auth Service.
    Dependency for protected endpoints.
    """
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    # Extract token from "Bearer <token>"
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning("Invalid Authorization header format")
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = parts[1]
    
    try:
        # Call Auth Service to verify token
        verify_url = f"{AUTH_SERVICE_URL}/auth/verify"
        payload = json.dumps({"token": token}).encode('utf-8')
        
        request = urllib.request.Request(
            verify_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode())
            
            if not result.get("valid"):
                logger.warning(f"Token verification failed: invalid token")
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            
            # Return the verified token info (username, user_id)
            logger.info(f"✓ Token verified for user: {result.get('username')}")
            return result
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        logger.error(f"Auth Service returned {e.code}: {error_body}")
        raise HTTPException(status_code=401, detail="Token verification failed")
    except urllib.error.URLError as e:
        logger.error(f"Failed to reach Auth Service: {str(e)}")
        raise HTTPException(status_code=503, detail="Auth Service unavailable")
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Token verification error: {str(e)}")

@app.get("/healthz")
async def liveness():
    """Liveness probe - always returns 200 if service is running"""
    return {"status": "alive"}

@app.get("/ready")
async def readiness():
    """Readiness probe - checks if service is ready to accept traffic"""
    return {"status": "ready", "storage": "in-memory"}

@app.get("/db-check")
async def db_check():
    """Check database connectivity"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            logger.info("✓ Database connectivity verified")
            return {"status": "connected", "database": "postgres"}
        except Exception as e:
            logger.error(f"Database check failed: {str(e)}")
            return {"status": "error", "database": "postgres", "error": str(e)}, 503
    else:
        return {"status": "unavailable", "database": "not_configured"}

@app.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint"""
    return {"service": "user-service", "version": "0.2.0", "users_count": len(users_db)}

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, token_info: dict = Depends(verify_token)):
    """Get a user by ID (requires valid JWT token)"""
    if user_id in users_db:
        logger.info(f"User {token_info.get('username')} retrieved user {user_id}")
        return users_db[user_id]
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/users", response_model=list[User])
async def list_users(token_info: dict = Depends(verify_token)):
    """List all users (requires valid JWT token)"""
    logger.info(f"User {token_info.get('username')} listed all users")
    return list(users_db.values())

@app.post("/users", response_model=User, status_code=201)
async def create_user(user: User, token_info: dict = Depends(verify_token)):
    """Create a new user (requires valid JWT token)"""
    users_db[user.id] = user
    logger.info(f"User {token_info.get('username')} created user {user.username}")
    return user

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
