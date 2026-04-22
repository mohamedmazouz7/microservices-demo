# DevOps & Kubernetes Learning Roadmap

This document outlines a structured learning path to understand microservices, containerization, and Kubernetes orchestration.

## 📋 Table of Contents

1. [Phase 1: Fundamentals](#phase-1-fundamentals)
2. [Phase 2: Containerization](#phase-2-containerization)
3. [Phase 3: Kubernetes & Orchestration](#phase-3-kubernetes--orchestration)
4. [Phase 4: Advanced Topics](#phase-4-advanced-topics)
5. [Phase 5: Production Ready](#phase-5-production-ready)

---

## Phase 1: Fundamentals

### 1.1 Understanding Microservices Architecture

**What:** Large applications broken into small, independent services

**Key Concepts:**
- Service decomposition
- Inter-service communication
- API contracts
- Service boundaries

**Learning Activity:**
```
Study the Online Boutique architecture:
- 11 independent microservices
- Each handles one business domain
- Services communicate via gRPC
- Stateless where possible, use Redis for state
```

**Resources:**
- Read: `docs/01-ARCHITECTURE.md`
- Reference: Google's Online Boutique
- Key Insight: Each service can be developed, deployed, and scaled independently

### 1.2 Communication Patterns

**gRPC vs REST:**
- **gRPC**: Used between internal services (performant, typed)
- **REST/HTTP**: Used for external APIs (simple, stateless)

**Online Boutique Example:**
```
Frontend (HTTP)
    ↓
Calls → CartService (gRPC)
        ProductService (gRPC)
        CheckoutService (gRPC)
        ... other services (gRPC)
```

---

## Phase 2: Containerization

### 2.1 Docker Fundamentals

**Why Containers?**
- Consistency: "Works on my machine" problem solved
- Portability: Run anywhere
- Efficiency: Lightweight vs VMs
- Scalability: Easy to replicate

**Key Concepts:**
```
Image (Blueprint) → Container (Running Instance)
     ↓
Dockerfile → Build → Image Registry → Pull → Run Container
```

### 2.2 Dockerfile Deep Dive

**Multi-stage Builds (Best Practice):**

```dockerfile
# Stage 1: Build
FROM golang:1.21 AS builder
WORKDIR /app
COPY . .
RUN go build -o app .

# Stage 2: Runtime (smaller image)
FROM alpine:latest
COPY --from=builder /app/app /app
CMD ["./app"]
```

**Benefits:**
- Smaller final images
- Build dependencies not included
- Faster deployments
- Better security

### 2.3 Security Best Practices

**Each microservice's Dockerfile should have:**

```dockerfile
# ✅ DO
FROM alpine:latest  # Small base image
RUN addgroup -g 1000 appuser && adduser -u 1000 -G appuser appuser
USER appuser  # Non-root user
HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1

# ❌ DON'T
FROM ubuntu:latest  # Heavy base image
USER root  # Running as root
# No health checks
```

### 2.4 Local Development with Docker Compose

**Structure:**
```yaml
version: '3.8'
services:
  frontend:
    build: ./src/frontend
    ports:
      - "8080:8080"
    environment:
      - PRODUCT_CATALOG_SERVICE_ADDR=productcatalog:3550
  
  productcatalog:
    build: ./src/productcatalogservice
    ports:
      - "3550:3550"
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

**Commands:**
```bash
docker-compose up -d      # Start services
docker-compose down       # Stop services
docker-compose logs -f    # View logs
docker-compose ps        # See running services
```

---

## Phase 3: Kubernetes & Orchestration

### 3.1 Kubernetes Basics

**What is Kubernetes?**
- Container orchestration platform
- Automates deployment, scaling, and management
- Abstracts underlying infrastructure
- Provides high availability and fault tolerance

**Key Resources:**

```
┌─────────────────── Cluster ──────────────────┐
│  ┌──────────────── Node 1 ────────────────┐  │
│  │  ┌─────────┐  ┌─────────┐  ┌────────┐  │  │
│  │  │ Pod     │  │ Pod     │  │ Pod    │  │  │
│  │  │ (app)   │  │ (app)   │  │(redis) │  │  │
│  │  └─────────┘  └─────────┘  └────────┘  │  │
│  └─────────────────────────────────────────┘  │
│                                               │
│  ┌──────────────── Node 2 ────────────────┐  │
│  │  ┌─────────┐  ┌─────────┐             │  │
│  │  │ Pod     │  │ Pod     │             │  │
│  │  │ (app)   │  │ (app)   │             │  │
│  │  └─────────┘  └─────────┘             │  │
│  └─────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

### 3.2 Core Kubernetes Objects

#### Pod (Smallest deployable unit)
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: frontend
spec:
  containers:
  - name: server
    image: gcr.io/project/frontend:latest
    ports:
    - containerPort: 8080
```

**Remember:** Almost never deploy Pods directly. Use higher-level objects!

#### Deployment (Manages Pods)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 3  # Desired number of Pods
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: server
        image: gcr.io/project/frontend:latest
        ports:
        - containerPort: 8080
```

**What Deployment Does:**
- Creates and manages Pods
- Handles rolling updates
- Scales up/down
- Maintains desired state

#### Service (Network abstraction)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  type: LoadBalancer  # Or ClusterIP, NodePort
  selector:
    app: frontend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
```

**Service Types:**
- **ClusterIP**: Internal only (default)
- **NodePort**: External via node IP + port
- **LoadBalancer**: External load balancer (cloud providers)
- **ExternalName**: Maps to external DNS

#### ConfigMap (Configuration)
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DATABASE_HOST: postgres.default.svc.cluster.local
  LOG_LEVEL: info
```

#### Secret (Sensitive Data)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  DATABASE_PASSWORD: cGFzc3dvcmQxMjM=  # base64 encoded
  API_KEY: c2VjcmV0a2V5MTIz
```

### 3.3 Kubernetes Deployment Workflow

**Step 1: Create manifests**
```yaml
# frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: server
        image: gcr.io/project/frontend:latest
```

**Step 2: Apply to cluster**
```bash
kubectl apply -f frontend-deployment.yaml
```

**Step 3: Verify deployment**
```bash
kubectl get pods                    # See all pods
kubectl get deployments             # See deployments
kubectl describe pod <pod-name>     # Details
kubectl logs <pod-name>             # View logs
```

### 3.4 Common Kubernetes Commands

```bash
# View resources
kubectl get nodes                   # Cluster nodes
kubectl get pods                    # Pods
kubectl get services                # Services
kubectl get deployments             # Deployments
kubectl get all                     # Everything in namespace

# Detailed info
kubectl describe pod <pod-name>
kubectl describe service <service-name>

# Logs and debugging
kubectl logs <pod-name>             # Last 100 lines
kubectl logs -f <pod-name>          # Follow logs
kubectl logs <pod-name> -c <container>  # Specific container
kubectl exec -it <pod-name> -- /bin/sh  # Shell access

# Scale deployments
kubectl scale deployment frontend --replicas=5

# Update image
kubectl set image deployment/frontend frontend=gcr.io/project/frontend:v2

# Rollback
kubectl rollout undo deployment/frontend

# Delete resources
kubectl delete pod <pod-name>
kubectl delete deployment frontend
```

---

## Phase 4: Advanced Topics

### 4.1 Package Management with Helm

**What is Helm?**
- Package manager for Kubernetes
- Templates for YAML manifests
- Version control for deployments
- Easy rollback

**Helm Chart Structure:**
```
online-boutique/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default values
├── templates/
│   ├── deployment.yaml     # Template
│   ├── service.yaml
│   ├── configmap.yaml
│   └── ...
└── charts/                 # Dependency charts
```

**Basic Commands:**
```bash
helm repo add myrepo https://charts.example.com
helm repo update
helm search repo myrepo
helm install my-release myrepo/chart
helm upgrade my-release myrepo/chart
helm uninstall my-release
helm rollback my-release 1
```

### 4.2 Environment-Specific Configurations with Kustomize

**Structure:**
```
kubernetes/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── dev/
│   │   ├── kustomization.yaml      # Adds dev config
│   │   └── patches/
│   ├── staging/
│   │   └── kustomization.yaml
│   └── production/
│       └── kustomization.yaml
```

**Apply environment:**
```bash
kubectl apply -k kubernetes/overlays/dev
kubectl apply -k kubernetes/overlays/production
```

---

## Phase 5: Production Ready

### 5.1 CI/CD Pipeline

**Workflow:**
```
Code Push → Tests → Build Image → Push Registry 
        → Deploy Dev → Deploy Staging → Deploy Prod
```

**GitHub Actions Example:**
```yaml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker image
        run: docker build -t app:latest .
      - name: Push to registry
        run: docker push gcr.io/project/app:latest
      - name: Deploy to K8s
        run: kubectl apply -f kubernetes/
```

### 5.2 Monitoring & Observability

**The Three Pillars:**
1. **Metrics**: CPU, memory, request count
2. **Logs**: Application events
3. **Traces**: Request path through services

**Tools:**
- Prometheus: Metrics collection
- Grafana: Visualization
- ELK Stack or Loki: Logging
- Jaeger: Distributed tracing

### 5.3 Security Best Practices

- **Pod Security Policies**: Restrict pod capabilities
- **RBAC**: Role-based access control
- **Network Policies**: Firewall rules
- **Secrets Management**: Proper credential handling
- **Image Scanning**: Check for vulnerabilities
- **Resource Quotas**: Prevent resource exhaustion

---

## Summary Table

| Phase | Topic | Key Tool | Command |
|-------|-------|----------|---------|
| 1 | Microservices | Design | N/A |
| 2 | Docker | Image Build | `docker build -t app .` |
| 2 | Docker Compose | Local Dev | `docker-compose up` |
| 3 | Kubernetes | Deploy | `kubectl apply -f app.yaml` |
| 3 | Services | Networking | `kubectl expose deployment app` |
| 4 | Helm | Package Mgmt | `helm install app chart/` |
| 4 | Kustomize | Env Config | `kubectl apply -k overlays/prod` |
| 5 | GitHub Actions | CI/CD | `.github/workflows/*.yaml` |
| 5 | Prometheus | Monitoring | `helm install prometheus` |

---

## 🎓 Next Steps

1. **Start with Phase 1**: Understand the architecture
2. **Build a Dockerfile**: Containerize a simple service
3. **Run locally**: Use Docker Compose
4. **Deploy to K8s**: Start with Minikube
5. **Add CI/CD**: Set up GitHub Actions
6. **Monitor**: Add Prometheus & Grafana

---

## 📚 References

- [Kubernetes Official Docs](https://kubernetes.io/docs/)
- [Docker Official Docs](https://docs.docker.com/)
- [Helm Official Docs](https://helm.sh/docs/)
- [gRPC Documentation](https://grpc.io/docs/)
- [Nana Janashvili's K8s Course](https://www.techworld-with-nana.com/)

**Happy Learning! 🚀**
