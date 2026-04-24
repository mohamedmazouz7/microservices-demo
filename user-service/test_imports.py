#!/usr/bin/env python3
"""Quick test to verify all dependencies are installed."""

try:
    import fastapi
    print("✓ fastapi imported successfully")
except ImportError as e:
    print(f"✗ fastapi import failed: {e}")

try:
    import uvicorn
    print("✓ uvicorn imported successfully")
except ImportError as e:
    print(f"✗ uvicorn import failed: {e}")

try:
    import sqlalchemy
    print("✓ sqlalchemy imported successfully")
except ImportError as e:
    print(f"✗ sqlalchemy import failed: {e}")

try:
    import psycopg2
    print("✓ psycopg2 imported successfully")
except ImportError as e:
    print(f"✗ psycopg2 import failed: {e}")

try:
    from sqlalchemy.dialects import postgresql
    print("✓ sqlalchemy postgresql dialect imported successfully")
except ImportError as e:
    print(f"✗ sqlalchemy postgresql dialect import failed: {e}")

print("\nAll critical dependencies check complete!")
