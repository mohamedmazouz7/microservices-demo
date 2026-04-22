# Docker & Containerization Guide

## 📚 Table of Contents

1. [Docker Fundamentals](#docker-fundamentals)
2. [Writing Dockerfiles](#writing-dockerfiles)
3. [Best Practices](#best-practices)
4. [Multi-stage Builds](#multi-stage-builds)
5. [Building & Pushing Images](#building--pushing-images)
6. [Docker Compose for Local Development](#docker-compose-for-local-development)

---

## Docker Fundamentals

### What is Docker?

**Container:** A lightweight, standalone, executable package containing:
- Application code
- Runtime dependencies
- System tools
- Libraries
- Configuration

**Benefits:**
```
Traditional VMs vs Containers:

VMs:                        Containers:
┌─────────────────┐        ┌─────────────────┐
│ App + OS Guest  │ 2GB    │ App + Libraries │ 100MB
├─────────────────┤        ├─────────────────┤
│ Hypervisor      │        │ Docker Engine   │
├─────────────────┤        ├─────────────────┤
│ Host OS         │        │ Host OS         │
├─────────────────┤        ├─────────────────┤
│ Hardware        │        │ Hardware        │
└─────────────────┘        └─────────────────┘

Overhead: 2-10GB           Overhead: 10-50MB
Boot time: Minutes         Boot time: Seconds
```

### Image vs Container

**Image:** Blueprint (read-only template)
```
Dockerfile → Build → Image → Layer 1 (Base OS)
                     File    Layer 2 (Dependencies)
                     System  Layer 3 (Application)
```

**Container:** Running instance
```
Image → Docker Run → Container (writable layer on top)
                     Process running inside
                     Network access
                     Volume mounts
```

### Docker Architecture

```
┌──────────────────────────────────────┐
│        Docker Client (CLI)           │
│  (docker build, run, ps, etc)        │
└────────────────────┬─────────────────┘
                     │ API
                     ▼
┌──────────────────────────────────────┐
│     Docker Daemon (Server)           │
│  (Manages images and containers)     │
├──────────────────────────────────────┤
│ Container Runtime                    │
│  ├─ Container 1 (Process)           │
│  ├─ Container 2 (Process)           │
│  └─ Container 3 (Process)           │
└──────────────────────────────────────┘
```

---

## Writing Dockerfiles

### Basic Dockerfile Structure

```dockerfile
# 1. Base Image
FROM ubuntu:22.04

# 2. Metadata
LABEL maintainer="your.email@example.com"
LABEL description="Online Boutique Frontend Service"

# 3. Set working directory
WORKDIR /app

# 4. Copy application code
COPY . .

# 5. Install dependencies
RUN apt-get update && \
    apt-get install -y golang && \
    rm -rf /var/cache/apt/*

# 6. Build application
RUN go build -o app .

# 7. Expose port
EXPOSE 8080

# 8. Set environment variables
ENV LOG_LEVEL=info
ENV PORT=8080

# 9. Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 10. Set non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# 11. Entry point
CMD ["./app"]
```

### Key Dockerfile Instructions

| Instruction | Purpose | Example |
|-------------|---------|---------|
| `FROM` | Base image | `FROM golang:1.21` |
| `WORKDIR` | Working directory | `WORKDIR /app` |
| `COPY` | Copy files | `COPY . .` |
| `RUN` | Execute command | `RUN go build -o app .` |
| `EXPOSE` | Document port | `EXPOSE 8080` |
| `ENV` | Environment variable | `ENV PORT=8080` |
| `USER` | Set user | `USER appuser` |
| `CMD` | Default command | `CMD ["./app"]` |
| `ENTRYPOINT` | Entry point | `ENTRYPOINT ["./app"]` |
| `HEALTHCHECK` | Health probe | `HEALTHCHECK CMD curl -f ...` |

### Understanding Layers

Every instruction creates a new layer:

```dockerfile
FROM ubuntu:22.04           # Layer 1: Base OS (100MB)
RUN apt-get update          # Layer 2: apt-get updates (10MB)
RUN apt-get install golang  # Layer 3: golang (500MB)
COPY . .                    # Layer 4: App code (5MB)
RUN go build -o app .       # Layer 5: Built binary (20MB)
CMD ["./app"]               # Layer 6: Metadata

Total: 635MB

# Docker uses layered filesystem
# Each layer is a delta from the previous
# Layers are reused across images
```

---

## Best Practices

### 1. Use Specific Base Image Tags (Not `latest`)

```dockerfile
# ❌ AVOID
FROM golang:latest
FROM ubuntu:latest

# ✅ GOOD
FROM golang:1.21-alpine3.19
FROM ubuntu:22.04
```

**Why:** Ensure reproducible builds and avoid surprises when upstream updates.

### 2. Minimize Image Size

```dockerfile
# ❌ LARGE IMAGE (1.5GB)
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y build-essential golang
COPY . .
RUN go build -o app .

# ✅ SMALL IMAGE (150MB)
FROM alpine:3.19
RUN apk add --no-cache go
COPY . .
RUN go build -o app .
```

**Size Comparison:**
- ubuntu:22.04 = 77MB
- golang:1.21-alpine = 245MB
- alpine:latest = 7MB

### 3. Run as Non-Root User

```dockerfile
# ❌ INSECURE (runs as root)
FROM alpine
COPY . .
CMD ["./app"]

# ✅ SECURE (non-root user)
FROM alpine
RUN addgroup -g 1000 appuser && adduser -u 1000 -G appuser appuser
COPY . .
USER appuser  # Switch to non-root
CMD ["./app"]
```

**Security Impact:**
- Root user: Full system access if container escapes
- Non-root user: Limited damage in security breach

### 4. Use .dockerignore

```dockerfile
# .dockerignore (like .gitignore)
.git
.gitignore
node_modules/
*.log
.env.local
tests/
__pycache__/
*.pyc
.DS_Store
```

**Benefits:**
- Smaller build context
- Faster builds
- Exclude secrets from image

### 5. Keep Layers Organized

```dockerfile
# ❌ MANY LAYERS (poor caching)
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y git
RUN apt-get install -y go

# ✅ FEWER LAYERS (better caching)
RUN apt-get update && \
    apt-get install -y \
    curl \
    git \
    go && \
    rm -rf /var/cache/apt/*
```

**Caching:** When one instruction changes, all subsequent layers are rebuilt. Fewer layers = better cache hit rate.

### 6. Order Instructions by Change Frequency

```dockerfile
# ✅ GOOD - stable instructions first
FROM golang:1.21-alpine
RUN apk add --no-cache curl
COPY go.mod go.sum ./  # Rarely changes
COPY . .               # Often changes
RUN go build -o app .

# Why? If source changes, only rebuild from COPY onward
# Dependencies (go.mod) are cached if unchanged
```

### 7. Health Checks

```dockerfile
# HTTP service
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# gRPC service
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD grpc_health_probe -addr=:50051 || exit 1

# Generic
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD ["ps", "aux"] | grep app || exit 1
```

---

## Multi-stage Builds

### The Problem

```dockerfile
# Single-stage build
FROM golang:1.21
WORKDIR /app
COPY . .
RUN go build -o app .
CMD ["./app"]

# Image size: 500MB+ (includes entire Go toolchain)
# Issue: Go compiler not needed at runtime!
```

### The Solution: Multi-stage Builds

```dockerfile
# Stage 1: Build
FROM golang:1.21 AS builder
WORKDIR /app
COPY . .
RUN go build -o app .

# Stage 2: Runtime (minimal image)
FROM alpine:3.19
RUN apk add --no-cache ca-certificates
WORKDIR /app
COPY --from=builder /app/app .
USER nobody
CMD ["./app"]

# Size comparison:
# Stage 1: 800MB (has compiler)
# Stage 2 final: 50MB (only binary!)
```

### Multi-stage for Different Services

#### Go Service Example
```dockerfile
FROM golang:1.21 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o app .

FROM scratch  # Empty base image!
COPY --from=builder /app/app /app
EXPOSE 8080
CMD ["./app"]
```

#### Node.js Service Example
```dockerfile
FROM node:20-alpine AS dependencies
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

#### Python Service Example
```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
USER nobody
CMD ["python", "app.py"]
```

---

## Building & Pushing Images

### Build an Image

```bash
# Basic build
docker build -t myapp:1.0 .

# Build with registry prefix
docker build -t gcr.io/my-project/myapp:1.0 .

# Build with labels
docker build \
  -t myapp:1.0 \
  --label version=1.0 \
  --label maintainer=your@email.com \
  .

# Build specific Dockerfile
docker build -f Dockerfile.prod -t myapp:1.0 .

# Build with build args
docker build \
  --build-arg VERSION=1.0 \
  --build-arg ENV=production \
  -t myapp:1.0 \
  .
```

### Push to Registry

```bash
# Tag image for registry
docker tag myapp:1.0 gcr.io/my-project/myapp:1.0
docker tag myapp:1.0 gcr.io/my-project/myapp:latest

# Login to registry
docker login gcr.io  # for Google Container Registry

# Push image
docker push gcr.io/my-project/myapp:1.0
docker push gcr.io/my-project/myapp:latest

# Check image
docker inspect gcr.io/my-project/myapp:1.0
```

### Image Naming Convention

```
registry.com/namespace/repository:tag

Examples:
┌─────────────────────────────────────────────┐
│ Docker Hub (no registry specified)          │
│ myapp:latest                                │
│ myusername/myapp:1.0                        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Google Container Registry (GCR)             │
│ gcr.io/my-project/myapp:1.0                │
│ us.gcr.io/my-project/myapp:1.0             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Amazon ECR                                  │
│ 123456789.dkr.ecr.us-east-1.amazonaws.com/ │
│ myapp:1.0                                   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Private Registry                            │
│ registry.mycompany.com/myapp:1.0           │
└─────────────────────────────────────────────┘
```

---

## Docker Compose for Local Development

### What is Docker Compose?

Tool for defining and running multi-container applications.

### Compose File Structure

```yaml
version: '3.8'

services:
  # Service 1
  frontend:
    build:
      context: ./src/frontend
      dockerfile: Dockerfile
    container_name: frontend
    ports:
      - "8080:8080"
    environment:
      - PRODUCT_CATALOG_ADDR=productcatalog:3550
      - CART_ADDR=cart:7070
    depends_on:
      - productcatalog
      - cart
    networks:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Service 2
  productcatalog:
    build:
      context: ./src/productcatalogservice
      dockerfile: Dockerfile
    container_name: productcatalog
    ports:
      - "3550:3550"
    networks:
      - backend

  # Service 3
  cart:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    networks:
      - backend

networks:
  backend:
    driver: bridge

volumes:
  redis_data:
```

### Common Docker Compose Commands

```bash
# Start services in background
docker-compose up -d

# Start services with output
docker-compose up

# View running services
docker-compose ps

# View logs
docker-compose logs -f              # all services
docker-compose logs -f frontend     # specific service

# Execute command in container
docker-compose exec frontend /bin/sh

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove volumes too
docker-compose down -v

# Rebuild images
docker-compose build

# Rebuild and restart
docker-compose up -d --build
```

### Docker Compose Environment Variables

```yaml
# Method 1: Inline
services:
  app:
    environment:
      - DATABASE_URL=postgres://localhost/db
      - LOG_LEVEL=info

# Method 2: .env file
# .env
DATABASE_URL=postgres://localhost/db
LOG_LEVEL=info

services:
  app:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - LOG_LEVEL=${LOG_LEVEL}

# Method 3: env_file
services:
  app:
    env_file:
      - .env
```

### Debugging with Docker Compose

```bash
# View specific service logs
docker-compose logs productcatalog --tail=50 -f

# Check service health
docker-compose ps

# Inspect network
docker network inspect online-boutique_backend

# Access shell inside container
docker-compose exec frontend sh
    $ ps aux              # see running processes
    $ curl localhost:8080 # test service
    $ exit

# Check resource usage
docker stats
```

---

## Hands-On Exercise

### Step 1: Write a Dockerfile

Create `src/frontend/Dockerfile`:
```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o app .

FROM alpine:3.19
RUN apk add --no-cache ca-certificates curl
WORKDIR /app
COPY --from=builder /app/app .
HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1
USER nobody
EXPOSE 8080
CMD ["./app"]
```

### Step 2: Build Image

```bash
cd src/frontend
docker build -t localhost:5000/frontend:1.0 .
docker images  # verify image was created
```

### Step 3: Run Container

```bash
docker run -p 8080:8080 localhost:5000/frontend:1.0
# Visit http://localhost:8080
```

### Step 4: Push to Registry

```bash
docker push localhost:5000/frontend:1.0
```

---

## Summary Table

| Aspect | Best Practice | Example |
|--------|---------------|---------|
| Base Image | Pin version | `FROM golang:1.21-alpine3.19` |
| Size | Multi-stage build | `AS builder` / `FROM scratch` |
| Security | Non-root user | `USER appuser` |
| Caching | Order by frequency | Dependencies before source |
| Health | Add healthchecks | `HEALTHCHECK CMD curl ...` |
| Registry | Use full paths | `gcr.io/project/app:1.0` |

---

**Next:** See [02-KUBERNETES.md](02-KUBERNETES.md) to learn about orchestration!
