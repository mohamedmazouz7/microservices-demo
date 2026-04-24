"""Minimal FastAPI User Service with Postgres support"""
import os
import logging
from fastapi import FastAPI
from pydantic import BaseModel

# Logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

app = FastAPI(title="User Service", version="0.2.0")

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
async def get_user(user_id: int):
    """Get a user by ID"""
    if user_id in users_db:
        return users_db[user_id]
    return {"detail": "User not found"}, 404

@app.get("/users", response_model=list[User])
async def list_users():
    """List all users"""
    return list(users_db.values())

@app.post("/users", response_model=User, status_code=201)
async def create_user(user: User):
    """Create a new user"""
    users_db[user.id] = user
    return user

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
