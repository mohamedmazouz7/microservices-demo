#!/bin/bash

# Setup script for microservices-demo project
# This script initializes the development environment

set -e

echo "🚀 Microservices Demo - Setup Script"
echo "===================================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check prerequisites
echo ""
echo "Checking prerequisites..."

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_status "Docker installed: $DOCKER_VERSION"
else
    print_error "Docker is not installed. Please install Docker Desktop."
    exit 1
fi

# Check kubectl
if command -v kubectl &> /dev/null; then
    KUBECTL_VERSION=$(kubectl version --client --short 2>/dev/null || echo "unknown")
    print_status "kubectl installed: $KUBECTL_VERSION"
else
    print_warning "kubectl is not installed. Install from: https://kubernetes.io/docs/tasks/tools/"
fi

# Check Minikube
if command -v minikube &> /dev/null; then
    print_status "Minikube installed: $(minikube version)"
else
    print_warning "Minikube not found. For local K8s, install from: https://minikube.sigs.k8s.io/docs/start/"
fi

# Check Helm
if command -v helm &> /dev/null; then
    print_status "Helm installed: $(helm version --short)"
else
    print_warning "Helm not found. Install from: https://helm.sh/docs/intro/install/"
fi

# Check Git
if command -v git &> /dev/null; then
    print_status "Git installed: $(git --version)"
else
    print_error "Git is not installed."
    exit 1
fi

# Create directories
echo ""
echo "Creating directory structure..."

DIRS=(
    "src/frontend"
    "src/cartservice"
    "src/productcatalogservice"
    "src/currencyservice"
    "src/paymentservice"
    "src/shippingservice"
    "src/emailservice"
    "src/checkoutservice"
    "src/recommendationservice"
    "src/adservice"
    "src/loadgenerator"
    "kubernetes/base/deployments"
    "kubernetes/base/services"
    "kubernetes/base/configmaps"
    "kubernetes/overlays/dev"
    "kubernetes/overlays/staging"
    "kubernetes/overlays/production"
    "helm/online-boutique/templates"
    "terraform/gke"
    "terraform/eks"
    "protos"
    "monitoring"
    ".github/workflows"
)

for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        print_status "Created: $dir"
    else
        print_warning "Already exists: $dir"
    fi
done

# Create .gitkeep files
echo ""
echo "Creating .gitkeep files..."

for dir in "${DIRS[@]}"; do
    touch "$dir/.gitkeep"
done

# Create environment file template
echo ""
echo "Creating configuration templates..."

cat > .env.example << 'EOF'
# Container Registry
REGISTRY=ghcr.io
REGISTRY_NAMESPACE=yourusername/microservices-demo

# Google Cloud (if using GCP)
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# Kubernetes
KUBE_CONTEXT=minikube
KUBE_NAMESPACE=online-boutique

# Application
ENVIRONMENT=development
LOG_LEVEL=info

# Services Configuration
PRODUCT_CATALOG_ADDR=productcatalog:3550
CART_ADDR=cartservice:7070
CURRENCY_ADDR=currencyservice:7000
PAYMENT_ADDR=paymentservice:5000
SHIPPING_ADDR=shippingservice:50051
EMAIL_ADDR=emailservice:8080
CHECKOUT_ADDR=checkoutservice:5050
RECOMMENDATION_ADDR=recommendationservice:8080
AD_ADDR=adservice:9555

# Database
DATABASE_HOST=postgres.default.svc.cluster.local
DATABASE_PORT=5432
DATABASE_NAME=boutique
DATABASE_USER=boutique
DATABASE_PASSWORD=changeme

# Redis
REDIS_ADDR=redis:6379

# External Services
ENABLE_PROFILER=false
ENABLE_TRACING=true
JAEGER_AGENT_ADDR=jaeger-agent:6831
EOF

print_status "Created .env.example"

# Create Docker Compose template
echo ""
echo "Creating docker-compose.yml template..."

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # Frontend
  frontend:
    build:
      context: ./src/frontend
      dockerfile: Dockerfile
    container_name: frontend
    ports:
      - "8080:8080"
    environment:
      - PRODUCT_CATALOG_ADDR=productcatalog:3550
      - CART_ADDR=cartservice:7070
    depends_on:
      - productcatalog
      - cartservice
    networks:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Product Catalog Service
  productcatalog:
    build:
      context: ./src/productcatalogservice
      dockerfile: Dockerfile
    container_name: productcatalog
    ports:
      - "3550:3550"
    networks:
      - backend

  # Cart Service
  cartservice:
    build:
      context: ./src/cartservice
      dockerfile: Dockerfile
    container_name: cartservice
    ports:
      - "7070:7070"
    environment:
      - REDIS_ADDR=redis:6379
    depends_on:
      - redis
    networks:
      - backend

  # Redis
  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    networks:
      - backend
    volumes:
      - redis_data:/data

networks:
  backend:
    driver: bridge

volumes:
  redis_data:
EOF

print_status "Created docker-compose.yml"

# Create .gitignore
echo ""
echo "Creating .gitignore..."

cat > .gitignore << 'EOF'
# Local development
.env
.env.local
*.log
.DS_Store
.vscode/
.idea/

# Docker
docker-compose.override.yml

# Kubernetes
kubeconfig
*.kubeconfig

# Terraform
terraform/.terraform
terraform/.terraform.lock.hcl
terraform/*.tfstate
terraform/*.tfstate.backup

# Go
bin/
dist/
*.exe
*.dll
*.so
*.dylib

# Node
node_modules/
dist/
build/

# Python
__pycache__/
*.py[cod]
*.egg-info/
venv/
env/

# Java
target/
*.class
*.jar

# IDE
*.swp
*.swo
*~
.project
.classpath

# Helm
Chart.lock
charts/

# CI/CD
.github/secrets

# OS
Thumbs.db
EOF

print_status "Created .gitignore"

# Initialize Git if not already initialized
if [ ! -d .git ]; then
    echo ""
    echo "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: project structure and documentation"
    print_status "Git repository initialized"
else
    print_warning "Git repository already exists"
fi

# Summary
echo ""
echo "===================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "===================================="
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and update values:"
echo "   cp .env.example .env"
echo ""
echo "2. Start local development with Docker Compose:"
echo "   docker-compose up -d"
echo ""
echo "3. For Kubernetes deployment, start Minikube:"
echo "   minikube start"
echo ""
echo "4. Deploy to local K8s:"
echo "   kubectl apply -k kubernetes/overlays/dev"
echo ""
echo "Documentation:"
echo "- Learning Roadmap: docs/00-LEARNING_ROADMAP.md"
echo "- Architecture: docs/01-ARCHITECTURE.md"
echo "- Docker Guide: docs/02-DOCKER.md"
echo "- Kubernetes Guide: docs/03-KUBERNETES.md"
echo "- CI/CD Guide: docs/04-CICD.md"
echo ""
echo "Happy learning! 🚀"
EOF
