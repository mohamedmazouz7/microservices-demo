import os
import logging
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/userdb")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()

# Logging setup
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="User Service", version="0.1.0")

# Lazy-loaded database objects (initialized on first use)
engine = None
SessionLocal = None
Base = declarative_base()

def get_engine():
    """Lazy-initialize the database engine."""
    global engine
    if engine is None:
        try:
            engine = create_engine(DATABASE_URL, pool_pre_ping=True)
            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {str(e)}")
            raise
    return engine

def get_session_local():
    """Lazy-initialize the session factory."""
    global SessionLocal
    if SessionLocal is None:
        engine = get_engine()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal

# Database models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic schemas
class UserCreate(BaseModel):
    username: str
    email: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

# Dependency: get DB session
def get_db():
    try:
        SessionLocal = get_session_local()
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to get database session: {str(e)}")
        raise

# Health check: basic liveness (no DB dependency)
@app.get("/healthz")
async def liveness():
    return {"status": "alive"}

# Readiness check: verify DB connectivity and create tables
@app.get("/ready")
async def readiness(db: Session = Depends(get_db)):
    try:
        # Simple query to verify DB is responsive
        db.execute(text("SELECT 1"))
        
        # Create tables if they don't exist (lazy initialization on first readiness check)
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        
        logger.info("Readiness check passed: DB is accessible and schema is ready")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Database not accessible: {str(e)}")

# Metrics endpoint (placeholder)
@app.get("/metrics")
async def metrics():
    return {"service": "user-service", "version": "0.1.0", "timestamp": datetime.utcnow().isoformat()}

# User endpoints
@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = User(username=user.username, email=user.email)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User created: {user.username}")
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        logger.warning(f"User {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/users", response_model=list[UserResponse])
async def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.username = user.username
    db_user.email = user.email
    db.commit()
    db.refresh(db_user)
    logger.info(f"User {user_id} updated")
    return db_user

@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    logger.info(f"User {user_id} deleted")
    return None

# Startup event: just log startup (DB connects on first request)
@app.on_event("startup")
async def startup_event():
    logger.info("User Service started successfully (DB will connect on first request)")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
