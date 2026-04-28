# Shop Microservices Architecture

## System Overview

This is a microservices-based e-commerce platform built on Kubernetes with 4 core services:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INGRESS (NGINX)                                      │
│                      shop.local (LoadBalancer)                               │
└──────────────┬────────────────┬────────────────┬──────────────┬──────────────┘
               │                │                │              │
               ▼                ▼                ▼              ▼
         ┌──────────┐      ┌──────────┐   ┌──────────┐    ┌──────────┐
         │ FRONTEND │      │   AUTH   │   │   USER   │    │ PRODUCT  │
         │ (Nginx)  │      │(FastAPI) │   │(FastAPI) │    │(FastAPI) │
         │  Port 80 │      │Port 8080 │   │Port 8080 │    │Port 8080 │
         └────┬─────┘      └────┬─────┘   └────┬─────┘    └────┬─────┘
              │                 │              │               │
              │                 │              │               │
         ┌────┴─────────────────┴──────────────┴───────────────┴────┐
         │                                                            │
         │          KUBERNETES CLUSTER (shop-zone namespace)         │
         │                                                            │
         └────────────────────────────────────────────────────────────┘
              │                 │              │               │
              │                 │              │               │
              ▼                 ▼              ▼               ▼
         ┌──────────┐      ┌──────────┐   ┌──────────┐    ┌──────────┐
         │  FRONTEND│      │AUTH  DB  │   │ USER DB  │    │PRODUCT DB│
         │(Static)  │      │ (Postgres)   │(Postgres)│    │(Postgres)│
         │  n/a     │      │Port 5432 │   │Port 5432 │    │Port 5432 │
         └──────────┘      └──────────┘   └──────────┘    └──────────┘
```

---

## Services & Responsibilities

### 1. **FRONTEND** (Nginx)
- **Port:** 80 (internal), http://shop.local/
- **Role:** User interface
- **Technology:** HTML5 + JavaScript (vanilla)
- **Responsibilities:**
  - Serve static web UI
  - Handle user login/logout
  - Display products list
  - Form to add new products
  - Store JWT token in browser localStorage

### 2. **AUTH SERVICE** (FastAPI)
- **Port:** 8080, http://auth-service.shop-zone.svc.cluster.local:8080
- **Endpoints:**
  - `POST /auth/login` — Issue JWT token
  - `POST /auth/verify` — Validate JWT token (called by other services)
  - `GET /healthz` — Health check
  - `GET /ready` — Readiness check
- **Responsibilities:**
  - Authenticate users (username/password)
  - Issue JWT tokens (HS256 algorithm)
  - Verify tokens for other services
  - Token validation for protected endpoints
- **Database:** Optional (currently stateless, uses hardcoded credentials)
- **No Database:** Auth service uses in-memory logic for demo

### 3. **USER SERVICE** (FastAPI)
- **Port:** 8080, http://user-service.shop-zone.svc.cluster.local:8080
- **Endpoints:**
  - `GET /users` — List all users (requires valid JWT)
  - `POST /users` — Create new user (requires valid JWT)
  - `GET /users/{id}` — Get user by ID (requires valid JWT)
  - `GET /healthz` — Health check
  - `GET /ready` — Readiness check
  - `GET /db-check` — Database connectivity check
- **Database:** PostgreSQL (postgres-db Service)
- **Responsibilities:**
  - Manage user records
  - Enforce JWT authentication
  - Call Auth Service to verify tokens

### 4. **PRODUCT SERVICE** (FastAPI)
- **Port:** 8080, http://product-service.shop-zone.svc.cluster.local:8080
- **Endpoints:**
  - `GET /products` — List all products (PUBLIC, no auth required)
  - `POST /products` — Create new product (requires valid JWT)
  - `GET /healthz` — Health check
  - `GET /ready` — Readiness check
  - `GET /db-check` — Database connectivity check
- **Database:** PostgreSQL (product-postgres-service Service)
- **Responsibilities:**
  - Manage product catalog
  - Allow public product browsing
  - Enforce JWT authentication for mutations
  - Call Auth Service to verify tokens

---

## Communication Flows

### **Flow 1: User Login**
```
Frontend (Browser)
    │
    ├─ POST /auth/login
    │  {"username": "testuser", "password": "testpass"}
    │
    └─► Auth Service
         │
         ├─ Generate JWT token (HS256)
         │
         └─► Frontend
             (stores token in localStorage)
             returns: {"access_token": "eyJhb...", "token_type": "bearer"}
```

---

### **Flow 2: View Products (No Auth Required)**
```
Frontend (Browser)
    │
    ├─ GET /products
    │  (no Authorization header)
    │
    ├─► Ingress (shop.local/products)
    │
    ├─► Product Service
    │   │
    │   └─ Query: SELECT * FROM products
    │
    ├─► Product DB (PostgreSQL)
    │
    └─► Frontend
        returns: [{"id": 1, "name": "Laptop", "price": 999.99, ...}, ...]
```

---

### **Flow 3: Add New Product (Requires Auth)**
```
Frontend (Browser)
    │
    ├─ POST /products
    │  Headers: Authorization: Bearer <JWT_TOKEN>
    │  Body: {"name": "Laptop", "description": "...", "price": 999.99}
    │
    ├─► Ingress (shop.local/products)
    │
    ├─► Product Service
    │   │
    │   ├─ Extract JWT from Authorization header
    │   │
    │   ├─ Call Auth Service /auth/verify
    │   │  POST body: {"token": "<JWT_TOKEN>"}
    │   │
    │   ├─► Auth Service
    │   │   │
    │   │   ├─ Validate JWT signature (HS256)
    │   │   │
    │   │   └─► Product Service
    │   │       returns: ✅ Valid token or ❌ Invalid token (401)
    │   │
    │   ├─ If valid:
    │   │  INSERT INTO products (name, description, price)
    │   │  VALUES ('Laptop', '...', 999.99)
    │   │
    │   ├─► Product DB (PostgreSQL)
    │   │
    │   └─► Frontend
    │       returns: {"id": 2, "name": "Laptop", ...}
    │
    └─ If invalid:
       returns: ❌ 401 Unauthorized
```

---

### **Flow 4: User Service (Similar Pattern)**
```
Frontend (Browser)
    │
    ├─ POST /users
    │  Headers: Authorization: Bearer <JWT_TOKEN>
    │  Body: {"username": "john", "email": "john@example.com"}
    │
    ├─► Ingress (shop.local/users)
    │
    ├─► User Service
    │   │
    │   ├─ Extract JWT from Authorization header
    │   │
    │   ├─ Call Auth Service /auth/verify
    │   │  POST body: {"token": "<JWT_TOKEN>"}
    │   │
    │   ├─► Auth Service (validates token)
    │   │
    │   ├─ If valid:
    │   │  INSERT INTO users (username, email)
    │   │
    │   ├─► User DB (PostgreSQL)
    │   │
    │   └─► User Service
    │       returns: {"id": 1, "username": "john", ...}
    │
    └─ Frontend returns: ✅ User created
```

---

## Database Architecture

### **Auth Service Database**
- **Name:** N/A (stateless, demo only)
- **Service:** None
- **Port:** N/A
- **Status:** No persistent storage (tokens are in-memory)

### **User Service Database**
- **Name:** shop_db
- **Service:** postgres-db (StatefulSet)
- **Port:** 5432
- **DNS:** postgres-db.shop-zone.svc.cluster.local:5432
- **Tables:**
  - `users` (id, username, email, created_at, etc.)

### **Product Service Database**
- **Name:** postgres (default DB)
- **Service:** product-postgres-service
- **Port:** 5432
- **DNS:** product-postgres-service.shop-zone.svc.cluster.local:5432
- **Tables:**
  - `products` (id, name, description, price, created_at)

---

## Network Communication Paths

### **Inside Kubernetes Cluster (Internal DNS)**

1. **Product Service → Auth Service**
   ```
   http://auth-service.shop-zone.svc.cluster.local:8080/auth/verify
   ```
   - Service Name: `auth-service`
   - Namespace: `shop-zone`
   - Port: `8080` (internal)

2. **Product Service → Product DB**
   ```
   postgres://postgres:PASSWORD@product-postgres-service:5432/postgres
   ```
   - Service Name: `product-postgres-service`
   - Port: `5432` (internal)

3. **User Service → Auth Service**
   ```
   http://auth-service.shop-zone.svc.cluster.local:8080/auth/verify
   ```

4. **User Service → User DB**
   ```
   postgres://postgres:PASSWORD@postgres-db:5432/shop_db
   ```

### **From Outside Cluster (Ingress)**

- **Client (Browser) → Ingress → Frontend**
  ```
  http://shop.local/ → 80
  ```

- **Client (Browser) → Ingress → Auth Service**
  ```
  http://shop.local/auth/login → Port 8080
  http://shop.local/auth/verify → Port 8080
  ```

- **Client (Browser) → Ingress → Product Service**
  ```
  http://shop.local/products → Port 8080
  ```

- **Client (Browser) → Ingress → User Service**
  ```
  http://shop.local/users → Port 8080
  ```

---

## Authentication & Authorization Flow (Detailed)

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                          │
└─────────────────────────────────────────────────────────────────┘

Step 1: Login (Get Token)
├─ User enters: username="testuser", password="testpass"
├─ POST /auth/login
├─► Auth Service validates credentials
└─► Returns: JWT token (HS256 signed)

Step 2: Store Token
├─ Frontend saves token in localStorage
└─ Token format: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Step 3: Use Token for Protected Endpoints
├─ Frontend sends: Authorization: Bearer <token>
├─ Ingress routes to service
├─► Service extracts token from header
├─► Service calls Auth Service /auth/verify
├─► Auth Service validates JWT signature
│   ├─ Checks: signature, expiration, claims
│   └─ Returns: ✅ Valid or ❌ Invalid
└─ Service allows/denies request based on response

Step 4: Public Endpoints (No Token)
├─ GET /products (no Authorization header needed)
├─► Product Service processes request immediately
└─► Returns: product list
```

---

## Service Dependencies

```
┌────────────────────────────────────────────────────┐
│              SERVICE DEPENDENCIES                  │
└────────────────────────────────────────────────────┘

Frontend
  ├─ Depends on: Ingress (router)
  ├─ Calls: Auth Service (/auth/login)
  ├─ Calls: Product Service (/products)
  └─ Calls: User Service (/users)

Auth Service
  ├─ Depends on: None (stateless)
  ├─ Called by: Product Service (verify)
  └─ Called by: User Service (verify)

Product Service
  ├─ Depends on: Product DB (PostgreSQL)
  ├─ Depends on: Auth Service (verify tokens)
  └─ Called by: Frontend (via Ingress)

User Service
  ├─ Depends on: User DB (PostgreSQL)
  ├─ Depends on: Auth Service (verify tokens)
  └─ Called by: Frontend (via Ingress)

Product DB
  ├─ Called by: Product Service only
  └─ Data: products table

User DB
  ├─ Called by: User Service only
  └─ Data: users table
```

---

## Request/Response Examples

### **1. Login Request**
```bash
POST /auth/login HTTP/1.1
Host: shop.local
Content-Type: application/json

{
  "username": "testuser",
  "password": "testpass"
}

Response (200 OK):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTc0NjAwMDAwMH0.signature",
  "token_type": "bearer"
}
```

### **2. Get Products (No Auth)**
```bash
GET /products HTTP/1.1
Host: shop.local

Response (200 OK):
[
  {
    "id": 1,
    "name": "Laptop",
    "description": "High-performance laptop",
    "price": 999.99,
    "created_at": "2026-04-28T10:30:00"
  },
  {
    "id": 2,
    "name": "Mouse",
    "description": "Wireless mouse",
    "price": 29.99,
    "created_at": "2026-04-28T11:00:00"
  }
]
```

### **3. Create Product (Requires Auth)**
```bash
POST /products HTTP/1.1
Host: shop.local
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "name": "Keyboard",
  "description": "Mechanical keyboard",
  "price": 149.99
}

Response (200 OK):
{
  "id": 3,
  "name": "Keyboard",
  "description": "Mechanical keyboard",
  "price": 149.99,
  "created_at": "2026-04-28T12:00:00"
}

Response (401 Unauthorized - if token invalid):
{
  "detail": "Invalid token"
}
```

---

## Data Flow Summary

| Flow | Source | → | Destination | Data | Auth Required |
|------|--------|---|-------------|------|---------------|
| Login | Frontend | → | Auth Service | username, password | ❌ No |
| View Products | Frontend | → | Product Service | — | ❌ No |
| Add Product | Frontend | → | Product Service | name, description, price | ✅ Yes |
| Verify Token | Product Service | → | Auth Service | token | ❌ No (service-to-service) |
| Query DB | Product Service | → | Product DB | SQL query | ❌ No (internal) |
| View Users | Frontend | → | User Service | — | ✅ Yes |
| Add User | Frontend | → | User Service | username, email | ✅ Yes |

---

## Key Security Points

1. **JWT Authentication:**
   - All write operations (POST) require valid JWT token
   - Auth Service signs tokens with HS256 secret
   - Services verify tokens by calling Auth Service

2. **Public vs Protected:**
   - `GET /products` — PUBLIC (anyone can view)
   - `POST /products` — PROTECTED (requires JWT)
   - `GET /users` — PROTECTED (requires JWT)
   - `POST /users` — PROTECTED (requires JWT)

3. **Token Verification:**
   - Each service calls Auth `/auth/verify` for protected endpoints
   - Auth Service validates signature and expiration
   - Invalid tokens return 401 Unauthorized

4. **Database Access:**
   - Credentials stored in Kubernetes Secrets
   - Services connect via internal cluster DNS
   - No external database access (only internal)

---

## Deployment Topology

```
┌─────────────────────────────────────────────────────────────┐
│                  Kubernetes Cluster                         │
│                  (shop-zone namespace)                      │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  INGRESS LAYER                                      │   │
│  │  ├─ shop-ingress (NGINX)                            │   │
│  │  └─ Routes:                                         │   │
│  │     ├─ / → frontend-service:80                      │   │
│  │     ├─ /auth → auth-service:8080                    │   │
│  │     ├─ /users → user-service:8080                   │   │
│  │     └─ /products → product-service:8080             │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  ┌────────────┬──────────────┬──────────────┬─────────┐    │
│  │ SERVICES   │              │              │         │    │
│  ├────────────┼──────────────┼──────────────┼─────────┤    │
│  │ frontend   │ auth-service │ user-service │ product │    │
│  │ (nginx)    │ (fastapi)    │ (fastapi)    │ service │    │
│  │ Pods: 1    │ Pods: 1      │ Pods: 2      │ Pods: 1 │    │
│  └────────────┴──────────────┴──────────────┴────────┬┘    │
│                                                        │     │
│  ┌────────────────────────────────────────────────────┘     │
│  │ STORAGE LAYER (Persistent Volumes)                      │
│  ├─ user-db-pvc → postgres-db (Shop DB)                    │
│  ├─ product-db-pvc → product-postgres-db (Products DB)     │
│  └─ auth-service (stateless, no storage)                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         │
         │ External Access
         ▼
    ┌─────────────────────┐
    │   Client Browser    │
    │  http://shop.local  │
    └─────────────────────┘
```

---

## Summary

**The architecture follows a microservices pattern:**

1. **Stateless Services** (Auth, Product, User) running in Kubernetes
2. **Database per Service** pattern (Product Service has its own DB, User Service has its own DB)
3. **Service-to-Service Communication** via internal DNS (cluster.local)
4. **JWT-based Security** with centralized Auth Service
5. **Ingress-based Routing** from external clients to internal services
6. **Nginx Frontend** serving static HTML/JS that communicates with backend APIs

**Key Principle:** Services are loosely coupled, communicate via HTTP/REST APIs, and maintain their own data stores. The Auth Service is the single source of truth for authentication.
