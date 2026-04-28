"""Minimal FastAPI Product Service with DB isolation and JWT-protected writes."""
import json
import logging
import os
import urllib.error
import urllib.request
from decimal import Decimal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


# ----------------------------
# Configuration
# ----------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DATABASE_URL = os.getenv("DATABASE_URL")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8080")

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(title="Product Service", version="0.1.0")


# ----------------------------
# Data Models
# ----------------------------
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=2000)
    price: Decimal = Field(..., gt=0)


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float


# ----------------------------
# DB Helpers
# ----------------------------
def get_db_connection():
    """Create a new DB connection on demand (simple and robust for this learning setup)."""
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL is not configured")

    try:
        import psycopg2

        conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
        return conn
    except Exception as exc:
        logger.error("DB connection failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


def init_products_table() -> None:
    """Initialize product table schema at startup."""
    schema_sql = """
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT DEFAULT '',
        price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(schema_sql)
        conn.commit()
        logger.info("✓ products table initialized")
    except HTTPException:
        logger.warning("Could not initialize products table at startup (service still starts)")
    except Exception as exc:
        logger.error("Failed to initialize products table: %s", exc)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# ----------------------------
# Auth Helpers
# ----------------------------
def verify_token(authorization: str = Header(default=None)) -> dict:
    """Verify JWT token by delegating to Auth Service /auth/verify."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = parts[1]
    verify_url = f"{AUTH_SERVICE_URL}/auth/verify"

    payload = json.dumps({"token": token}).encode("utf-8")
    request = urllib.request.Request(
        verify_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
            if not result.get("valid"):
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            return result
    except urllib.error.HTTPError:
        raise HTTPException(status_code=401, detail="Token verification failed")
    except urllib.error.URLError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")


# ----------------------------
# Basic Endpoints
# ----------------------------
@app.on_event("startup")
def on_startup() -> None:
    logger.info("Product Service starting...")
    init_products_table()


@app.get("/healthz")
def liveness():
    return {"status": "alive"}


@app.get("/ready")
def readiness():
    # Basic readiness (DB checked by /db-check and endpoint operations)
    return {"status": "ready"}


@app.get("/db-check")
def db_check():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        return {"status": "connected"}
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# ----------------------------
# Product Endpoints
# ----------------------------
@app.get("/products", response_model=list[ProductResponse])
def list_products():
    """Public endpoint (no token required)."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, description, price FROM products ORDER BY id ASC")
        rows = cur.fetchall()

        return [
            ProductResponse(
                id=row[0],
                name=row[1],
                description=row[2] or "",
                price=float(row[3]),
            )
            for row in rows
        ]
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.post("/products", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, token_info: dict = Depends(verify_token)):
    """Protected endpoint (requires valid JWT)."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO products (name, description, price)
            VALUES (%s, %s, %s)
            RETURNING id, name, description, price
            """,
            (product.name, product.description, product.price),
        )
        row = cur.fetchone()
        conn.commit()

        logger.info("User %s created product %s", token_info.get("username"), row[1])

        return ProductResponse(
            id=row[0],
            name=row[1],
            description=row[2] or "",
            price=float(row[3]),
        )
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
