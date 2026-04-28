# Product Service

Minimal FastAPI Product Service following the existing pattern.

## Endpoints

- `GET /products` (Public)
- `POST /products` (Protected - requires `Authorization: Bearer <JWT>`)
- `GET /healthz`
- `GET /ready`
- `GET /db-check`

## Environment Variables

- `PORT` (default: `8080`)
- `LOG_LEVEL` (default: `INFO`)
- `DATABASE_URL` (**required**) e.g. `postgres://user:password@postgres-product.shop-zone.svc.cluster.local:5432/product_db`
- `AUTH_SERVICE_URL` (**required for protected writes**) e.g. `http://auth-service.shop-zone.svc.cluster.local:8080`

## Table Schema (initialized on startup)

```sql
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Quick Local Run

```bash
docker build -t product-service:local .
docker run --rm -p 8080:8080 \
  -e DATABASE_URL="postgres://user:password@host.docker.internal:5432/product_db" \
  -e AUTH_SERVICE_URL="http://host.docker.internal:8081" \
  product-service:local
```
