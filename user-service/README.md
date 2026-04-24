# User Service

A simple FastAPI-based microservice for managing user profiles, connected to PostgreSQL.

## Features
- CRUD endpoints for users (`POST /users`, `GET /users/{id}`, `PUT /users/{id}`, `DELETE /users/{id}`)
- Health check endpoints (`/healthz` for liveness, `/ready` for readiness with DB connectivity check)
- Metrics endpoint (`/metrics`)
- Auto-creates database schema on startup
- Non-root container user for security
- Multi-stage Docker build for minimal image size

## Environment Variables
- `DATABASE_URL` (required): PostgreSQL connection string, e.g., `postgresql://user:password@postgres.default.svc.cluster.local:5432/userdb`
- `PORT` (optional, default: 8080): Port the service listens on
- `LOG_LEVEL` (optional, default: info): Logging level (debug, info, warning, error)

## Local Testing

### Build the Docker image
```bash
cd /home/nirou/K8s/microservices/micro/user-service
docker build -t your-dockerhub-username/user-service:0.1.0 .
```

### Run locally with Docker (requires a running Postgres instance)
```bash
docker run -p 8080:8080 \
  -e DATABASE_URL="postgresql://user:password@host.docker.internal:5432/userdb" \
  your-dockerhub-username/user-service:0.1.0
```

### Test endpoints
```bash
# Health check
curl http://localhost:8080/healthz

# Readiness (checks DB)
curl http://localhost:8080/ready

# Create a user
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "email": "john@example.com"}'

# List users
curl http://localhost:8080/users

# Get specific user
curl http://localhost:8080/users/1
```

## Push to Docker Hub

```bash
# Login to Docker Hub
docker login

# Tag the image
docker tag your-dockerhub-username/user-service:0.1.0 your-dockerhub-username/user-service:latest

# Push
docker push your-dockerhub-username/user-service:0.1.0
docker push your-dockerhub-username/user-service:latest
```

## Update Kubernetes Deployment
After pushing to Docker Hub, update your `user-service-deployment.yaml`:
```yaml
image: your-dockerhub-username/user-service:0.1.0
```

Then apply:
```bash
kubectl apply -f user-service-deployment.yaml
```

## Image size
Multi-stage build keeps the final image ~300-400MB (Python base + dependencies), suitable for Kubernetes.
