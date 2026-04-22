.PHONY: help setup build push deploy dev-up dev-down k8s-up k8s-down logs clean

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help:
	@echo "$(GREEN)Microservices Demo - Makefile Commands$(NC)"
	@echo ""
	@echo "Setup & Environment:"
	@echo "  make setup          - Initialize project structure"
	@echo "  make init           - Install dependencies"
	@echo ""
	@echo "Docker Local Development:"
	@echo "  make dev-up         - Start services with Docker Compose"
	@echo "  make dev-down       - Stop all services"
	@echo "  make dev-logs       - View Docker Compose logs"
	@echo "  make dev-clean      - Remove all containers and volumes"
	@echo ""
	@echo "Kubernetes Development (Minikube):"
	@echo "  make k8s-up         - Start Minikube and deploy to dev"
	@echo "  make k8s-down       - Stop Minikube"
	@echo "  make k8s-deploy     - Deploy to dev cluster"
	@echo "  make k8s-logs       - View Kubernetes logs"
	@echo "  make k8s-shell      - Open shell in frontend pod"
	@echo "  make k8s-scale      - Scale frontend to 5 replicas"
	@echo "  make k8s-dashboard  - Open Kubernetes dashboard"
	@echo ""
	@echo "Building & Pushing:"
	@echo "  make build          - Build all Docker images"
	@echo "  make build-service  - Build specific service (SERVICE=frontend)"
	@echo "  make push           - Push all images to registry"
	@echo "  make clean          - Remove local images"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests"
	@echo "  make test-go        - Run Go tests"
	@echo "  make test-node      - Run Node.js tests"
	@echo "  make test-python    - Run Python tests"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy-prod    - Deploy to production"
	@echo "  make deploy-staging - Deploy to staging"
	@echo "  make rollback       - Rollback last deployment"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs           - Open documentation in browser"
	@echo ""

# ============================================================================
# SETUP & INITIALIZATION
# ============================================================================

setup:
	@echo "$(GREEN)Setting up project structure...$(NC)"
	@chmod +x scripts/setup.sh
	@scripts/setup.sh
	@echo "$(GREEN)✓ Project setup complete!$(NC)"

init: setup
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@echo "  - Docker: Already assumed installed"
	@echo "  - kubectl: $(shell kubectl version --client --short 2>/dev/null || echo 'Not installed - install from https://kubernetes.io/docs/tasks/tools/')"
	@echo "  - Minikube: $(shell minikube version 2>/dev/null || echo 'Not installed - install from https://minikube.sigs.k8s.io/docs/start/')"
	@echo "  - Helm: $(shell helm version --short 2>/dev/null || echo 'Not installed - install from https://helm.sh/docs/intro/install/')"
	@echo "$(GREEN)✓ Dependencies check complete!$(NC)"

# ============================================================================
# DOCKER COMPOSE - LOCAL DEVELOPMENT
# ============================================================================

dev-up:
	@echo "$(GREEN)Starting services with Docker Compose...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✓ Services started!$(NC)"
	@echo "Frontend: http://localhost:8080"
	@sleep 3
	@docker-compose ps

dev-down:
	@echo "$(YELLOW)Stopping services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

dev-logs:
	@docker-compose logs -f

dev-build:
	@echo "$(GREEN)Building Docker images...$(NC)"
	@docker-compose build
	@echo "$(GREEN)✓ Build complete!$(NC)"

dev-clean:
	@echo "$(RED)Removing all containers and volumes...$(NC)"
	@docker-compose down -v
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"

dev-shell:
	@docker-compose exec frontend sh

# ============================================================================
# KUBERNETES - MINIKUBE DEVELOPMENT
# ============================================================================

k8s-up:
	@echo "$(GREEN)Starting Minikube...$(NC)"
	@minikube start --cpus=4 --memory=8192
	@echo "$(GREEN)✓ Minikube started!$(NC)"
	@make k8s-deploy

k8s-down:
	@echo "$(YELLOW)Stopping Minikube...$(NC)"
	@minikube stop
	@echo "$(GREEN)✓ Minikube stopped$(NC)"

k8s-deploy:
	@echo "$(GREEN)Deploying to development cluster...$(NC)"
	@kubectl apply -k kubernetes/overlays/dev
	@echo "$(GREEN)Waiting for rollout...$(NC)"
	@kubectl rollout status deployment/frontend -n online-boutique --timeout=5m || true
	@echo "$(GREEN)✓ Deployment complete!$(NC)"
	@make k8s-info

k8s-deploy-prod:
	@echo "$(GREEN)Deploying to production cluster...$(NC)"
	@kubectl apply -k kubernetes/overlays/production
	@kubectl rollout status deployment/frontend -n online-boutique --timeout=10m
	@echo "$(GREEN)✓ Production deployment complete!$(NC)"

k8s-info:
	@echo ""
	@echo "$(GREEN)Kubernetes Cluster Info:$(NC)"
	@echo "Pods:"
	@kubectl get pods -n online-boutique
	@echo ""
	@echo "Services:"
	@kubectl get svc -n online-boutique
	@echo ""
	@echo "To access frontend:"
	@echo "  kubectl port-forward svc/frontend 8080:80 -n online-boutique"

k8s-logs:
	@kubectl logs -f deployment/frontend -n online-boutique

k8s-shell:
	@POD=$$(kubectl get pod -n online-boutique -l app=frontend -o jsonpath='{.items[0].metadata.name}'); \
	echo "$(GREEN)Opening shell in pod: $$POD$(NC)"; \
	kubectl exec -it $$POD -n online-boutique -- sh

k8s-scale:
	@echo "$(GREEN)Scaling frontend to 5 replicas...$(NC)"
	@kubectl scale deployment frontend --replicas=5 -n online-boutique
	@kubectl get pods -n online-boutique -w

k8s-dashboard:
	@echo "$(GREEN)Opening Minikube dashboard...$(NC)"
	@minikube dashboard

k8s-delete:
	@echo "$(RED)Deleting namespace and all resources...$(NC)"
	@kubectl delete namespace online-boutique
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"

# ============================================================================
# DOCKER BUILD & PUSH
# ============================================================================

build:
	@echo "$(GREEN)Building all Docker images...$(NC)"
	@for service in frontend cartservice productcatalogservice currencyservice paymentservice shippingservice emailservice checkoutservice recommendationservice adservice loadgenerator; do \
		if [ -d "src/$$service" ]; then \
			echo "Building $$service..."; \
			docker build -t ghcr.io/yourusername/$$service:latest src/$$service || exit 1; \
		fi \
	done
	@echo "$(GREEN)✓ All images built!$(NC)"

build-service:
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)Error: SERVICE not specified$(NC)"; \
		echo "Usage: make build-service SERVICE=frontend"; \
		exit 1; \
	fi
	@echo "$(GREEN)Building $(SERVICE)...$(NC)"
	@docker build -t ghcr.io/yourusername/$(SERVICE):latest src/$(SERVICE)
	@echo "$(GREEN)✓ $(SERVICE) built!$(NC)"

push:
	@echo "$(GREEN)Pushing all images to registry...$(NC)"
	@for service in frontend cartservice productcatalogservice currencyservice paymentservice shippingservice emailservice checkoutservice recommendationservice adservice loadgenerator; do \
		if [ -d "src/$$service" ]; then \
			echo "Pushing $$service..."; \
			docker push ghcr.io/yourusername/$$service:latest || exit 1; \
		fi \
	done
	@echo "$(GREEN)✓ All images pushed!$(NC)"

clean:
	@echo "$(RED)Removing all local images...$(NC)"
	@docker rmi -f $$(docker images -q ghcr.io/yourusername/*) 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"

# ============================================================================
# TESTING
# ============================================================================

test:
	@echo "$(GREEN)Running all tests...$(NC)"
	@make test-go
	@make test-node
	@make test-python
	@echo "$(GREEN)✓ All tests passed!$(NC)"

test-go:
	@echo "$(GREEN)Running Go tests...$(NC)"
	@for dir in src/frontend src/productcatalogservice src/checkoutservice src/shippingservice; do \
		if [ -d "$$dir" ]; then \
			echo "Testing $$dir..."; \
			cd "$$dir" && go test -v -race -coverprofile=coverage.out ./... || exit 1; \
			cd - > /dev/null; \
		fi \
	done

test-node:
	@echo "$(GREEN)Running Node.js tests...$(NC)"
	@for dir in src/currencyservice src/paymentservice; do \
		if [ -d "$$dir" ] && [ -f "$$dir/package.json" ]; then \
			echo "Testing $$dir..."; \
			cd "$$dir" && npm ci && npm test || exit 1; \
			cd - > /dev/null; \
		fi \
	done

test-python:
	@echo "$(GREEN)Running Python tests...$(NC)"
	@for dir in src/emailservice src/recommendationservice; do \
		if [ -d "$$dir" ] && [ -f "$$dir/requirements.txt" ]; then \
			echo "Testing $$dir..."; \
			cd "$$dir" && pip install -r requirements.txt && pip install pytest && pytest || exit 1; \
			cd - > /dev/null; \
		fi \
	done

# ============================================================================
# DEPLOYMENT
# ============================================================================

deploy-staging:
	@echo "$(GREEN)Deploying to staging...$(NC)"
	@kubectl apply -k kubernetes/overlays/staging
	@kubectl rollout status deployment/frontend -n online-boutique --timeout=5m
	@echo "$(GREEN)✓ Staging deployment complete!$(NC)"

deploy-prod:
	@echo "$(RED)⚠️  Deploying to PRODUCTION!$(NC)"
	@echo "Press Ctrl+C to cancel (5 second delay)"
	@sleep 5
	@kubectl apply -k kubernetes/overlays/production
	@kubectl rollout status deployment/frontend -n online-boutique --timeout=10m
	@echo "$(GREEN)✓ Production deployment complete!$(NC)"

rollback:
	@echo "$(YELLOW)Rolling back last deployment...$(NC)"
	@kubectl rollout undo deployment/frontend -n online-boutique
	@kubectl rollout status deployment/frontend -n online-boutique
	@echo "$(GREEN)✓ Rollback complete!$(NC)"

# ============================================================================
# DOCUMENTATION
# ============================================================================

docs:
	@echo "$(GREEN)Opening documentation...$(NC)"
	@open file://$(PWD)/docs/README.md 2>/dev/null || \
	xdg-open file://$(PWD)/docs/README.md 2>/dev/null || \
	echo "Open $(PWD)/docs/README.md in your browser"

# ============================================================================
# UTILITY
# ============================================================================

.DEFAULT_GOAL := help

.PHONY: help $(MAKECMDGOALS)
