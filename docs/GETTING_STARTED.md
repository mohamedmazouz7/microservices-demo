# Getting Started Guide

## Prerequisites

### Required
- Docker Desktop or Docker Engine (v20.10+)
- kubectl (v1.24+)
- Git

### Optional (but recommended)
- Minikube or Kind (local Kubernetes)
- Helm 3+ (package management)
- Terraform (infrastructure as code)
- GitHub CLI (for CI/CD)

## Installation

### 1. Docker

**macOS/Windows:**
```bash
# Download from https://www.docker.com/products/docker-desktop
# Or install via Homebrew
brew install --cask docker
```

**Linux (Ubuntu):**
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker $USER
newgrp docker
```

### 2. kubectl

```bash
# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Verify
kubectl version --client
```

### 3. Minikube (for local Kubernetes)

```bash
# macOS
brew install minikube

# Linux
curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Start Minikube
minikube start
minikube dashboard  # Opens Kubernetes dashboard
```

### 4. Helm (optional)

```bash
# macOS
brew install helm

# Linux
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify
helm version
```

## Quick Start (5 minutes)

### Option 1: Docker Compose (Easiest)

```bash
# Clone the repository
git clone https://github.com/yourusername/microservices-demo.git
cd microservices-demo

# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Start services
docker-compose up -d

# Check services
docker-compose ps

# View logs
docker-compose logs -f frontend

# Access frontend
open http://localhost:8080

# Stop services
docker-compose down
```

### Option 2: Minikube + kubectl (Recommended for Learning)

```bash
# Start Minikube
minikube start --cpus=4 --memory=8192

# Verify cluster
kubectl cluster-info
kubectl get nodes

# Deploy application
kubectl apply -k kubernetes/overlays/dev

# Check deployment
kubectl get pods -n online-boutique
kubectl get svc -n online-boutique

# Port forward to frontend
kubectl port-forward svc/frontend 8080:80 -n online-boutique

# Access frontend
open http://localhost:8080

# View logs
kubectl logs -f deployment/frontend -n online-boutique

# Scale deployment
kubectl scale deployment frontend --replicas=5 -n online-boutique

# Clean up
kubectl delete namespace online-boutique
minikube stop
```

### Option 3: GKE (Google Kubernetes Engine)

```bash
# Set up GCP
export PROJECT_ID="your-project-id"
export REGION="us-central1"

gcloud config set project $PROJECT_ID
gcloud services enable container.googleapis.com

# Create cluster
gcloud container clusters create online-boutique \
  --region=$REGION \
  --num-nodes=3 \
  --machine-type=n1-standard-2

# Get credentials
gcloud container clusters get-credentials online-boutique --region=$REGION

# Deploy
kubectl apply -k kubernetes/overlays/production

# Get external IP
kubectl get svc frontend -n online-boutique -w

# Access (wait for external IP to be assigned)
open http://EXTERNAL_IP
```

## Project Structure

```
microservices-demo/
├── docs/                    # Learning materials
│   ├── 00-LEARNING_ROADMAP.md
│   ├── 01-ARCHITECTURE.md
│   ├── 02-DOCKER.md
│   ├── 03-KUBERNETES.md
│   ├── 04-CICD.md
│   └── ...
├── src/                     # Source code
│   ├── frontend/
│   ├── cartservice/
│   └── ...
├── kubernetes/              # K8s manifests
│   ├── base/
│   ├── overlays/
│   └── ...
├── helm/                    # Helm charts
├── terraform/               # Infrastructure as Code
├── .github/workflows/       # CI/CD pipelines
├── scripts/                 # Utility scripts
├── docker-compose.yml       # Local development
└── README.md               # This file
```

## Common Tasks

### View Application

**Local (Docker Compose):**
```bash
open http://localhost:8080
```

**Minikube:**
```bash
kubectl port-forward svc/frontend 8080:80 -n online-boutique
open http://localhost:8080
```

**GKE:**
```bash
# Get external IP
kubectl get svc frontend -n online-boutique

# Open in browser
open http://<EXTERNAL_IP>
```

### View Logs

```bash
# Docker Compose
docker-compose logs -f frontend

# Kubernetes
kubectl logs -f deployment/frontend -n online-boutique

# Specific container
kubectl logs -f deployment/frontend -n online-boutique -c frontend
```

### Scale Services

```bash
# Docker Compose - manual (just change docker-compose.yml)

# Kubernetes - manual
kubectl scale deployment frontend --replicas=5 -n online-boutique

# Kubernetes - automatic
kubectl autoscale deployment frontend --min=2 --max=10 --cpu-percent=70 -n online-boutique
```

### Update Application

```bash
# Change source code, then rebuild

# Docker Compose
docker-compose build frontend
docker-compose up -d frontend

# Kubernetes - update image
kubectl set image deployment/frontend frontend=new-image:v1.0 -n online-boutique

# Watch rollout
kubectl rollout status deployment/frontend -n online-boutique
```

### Rollback

```bash
# Kubernetes
kubectl rollout undo deployment/frontend -n online-boutique
kubectl rollout history deployment/frontend -n online-boutique
```

## Environment Configuration

### Using .env File

```bash
# Copy example
cp .env.example .env

# Edit configuration
nano .env

# Docker Compose will automatically load .env
docker-compose up -d
```

### Kubernetes ConfigMap

```bash
# View configuration
kubectl get configmap app-config -n online-boutique -o yaml

# Update configuration
kubectl edit configmap app-config -n online-boutique

# Restart pods to pick up changes
kubectl rollout restart deployment/frontend -n online-boutique
```

## Cleanup

### Docker Compose

```bash
# Stop services
docker-compose down

# Remove volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

### Kubernetes

```bash
# Delete all resources
kubectl delete namespace online-boutique

# For Minikube
minikube stop
minikube delete
```

### GKE

```bash
# Delete cluster (careful!)
gcloud container clusters delete online-boutique --region=$REGION

# Delete persistent volumes
kubectl delete pvc --all -n online-boutique
```

## Troubleshooting

### Pod not starting?

```bash
# Check pod status
kubectl describe pod <pod-name> -n online-boutique

# View pod logs
kubectl logs <pod-name> -n online-boutique

# Check events
kubectl get events -n online-boutique --sort-by='.lastTimestamp'
```

### Service not accessible?

```bash
# Check service
kubectl get svc -n online-boutique
kubectl describe svc frontend -n online-boutique

# Test connectivity
kubectl run -it --rm debug --image=alpine --restart=Never -- \
  wget http://frontend.online-boutique.svc.cluster.local
```

### Image pull errors?

```bash
# Check image exists
kubectl get pods -n online-boutique -o jsonpath='{.items[*].spec.containers[*].image}'

# Check image pull policy
kubectl get pods -n online-boutique -o jsonpath='{.items[*].spec.containers[*].imagePullPolicy}'

# Pull image manually
docker pull <image>
```

## Learning Path

1. **Docker Basics** → docs/02-DOCKER.md
   - Understand containerization
   - Write Dockerfiles
   - Run containers locally

2. **Docker Compose** → docker-compose.yml
   - Multi-container applications
   - Service networking
   - Local development

3. **Kubernetes Basics** → docs/03-KUBERNETES.md
   - Understand orchestration
   - Deploy applications
   - Scale and manage

4. **Configuration Management** → kubernetes/overlays/
   - Environment-specific configs
   - Kustomize overlays
   - Helm charts

5. **CI/CD** → docs/04-CICD.md
   - GitHub Actions
   - Automated testing
   - Automated deployment

6. **Production Readiness** → kubernetes/overlays/production/
   - Monitoring
   - Logging
   - Security
   - Disaster recovery

## Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Helm Documentation](https://helm.sh/docs/)
- [gRPC Documentation](https://grpc.io/docs/)
- [Nana's Kubernetes Course](https://www.techworld-with-nana.com/)

## Next Steps

1. ✅ Follow this guide to set up your environment
2. 📚 Read the learning roadmap: [docs/00-LEARNING_ROADMAP.md](docs/00-LEARNING_ROADMAP.md)
3. 🏗️ Understand the architecture: [docs/01-ARCHITECTURE.md](docs/01-ARCHITECTURE.md)
4. 🐳 Learn Docker: [docs/02-DOCKER.md](docs/02-DOCKER.md)
5. ☸️ Learn Kubernetes: [docs/03-KUBERNETES.md](docs/03-KUBERNETES.md)

**Happy learning! 🚀**
