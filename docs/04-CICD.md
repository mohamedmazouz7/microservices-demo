# CI/CD Pipeline with GitHub Actions

## 📚 Table of Contents

1. [GitHub Actions Basics](#github-actions-basics)
2. [Build & Push Pipeline](#build--push-pipeline)
3. [Test Pipeline](#test-pipeline)
4. [Deployment Pipeline](#deployment-pipeline)
5. [Complete Workflow](#complete-workflow)

---

## GitHub Actions Basics

### Workflow Structure

```yaml
name: Workflow Name                    # Display name

on:                                    # Trigger events
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:                                  # Define jobs
  job-name:                           # Job identifier
    runs-on: ubuntu-latest            # Runner environment
    steps:                            # Steps to execute
    - name: Step name
      run: echo "Hello World"
```

### Available Runners

- `ubuntu-latest` (Ubuntu 22.04)
- `windows-latest` (Windows Server 2022)
- `macos-latest` (macOS 13.x)
- Self-hosted runners

---

## Build & Push Pipeline

### Step 1: Build Docker Image

```yaml
name: Build Docker Image

on:
  push:
    branches: [main]
    paths:
    - 'src/frontend/**'
    - '.github/workflows/build-frontend.yml'

env:
  REGISTRY: gcr.io
  PROJECT_ID: my-project
  IMAGE_NAME: frontend

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    # Checkout code
    - name: Checkout code
      uses: actions/checkout@v4
    
    # Setup Docker Buildx
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    # Login to Google Container Registry
    - name: Authenticate to Google Cloud
      uses: google-github-actions/auth@v2
      with:
        credentials_json: ${{ secrets.GCP_SERVICE_ACCOUNT }}
    
    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v2
    
    - name: Configure Docker for GCR
      run: gcloud auth configure-docker ${{ env.REGISTRY }}
    
    # Build and push image
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: ./src/frontend
        file: ./src/frontend/Dockerfile
        push: true
        tags: |
          ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/${{ env.IMAGE_NAME }}:latest
        cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/${{ env.IMAGE_NAME }}:buildcache
        cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/${{ env.IMAGE_NAME }}:buildcache,mode=max
```

### Step 2: Build All Services

```yaml
name: Build All Services

on:
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  REGISTRY_USERNAME: ${{ github.actor }}
  REGISTRY_PASSWORD: ${{ secrets.GITHUB_TOKEN }}

jobs:
  build-services:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service:
        - frontend
        - cartservice
        - productcatalogservice
        - currencyservice
        - paymentservice
        - shippingservice
        - emailservice
        - checkoutservice
        - recommendationservice
        - adservice
    
    steps:
    - uses: actions/checkout@v4
    
    - uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ env.REGISTRY_USERNAME }}
        password: ${{ env.REGISTRY_PASSWORD }}
    
    - name: Build and push ${{ matrix.service }}
      uses: docker/build-push-action@v5
      with:
        context: ./src/${{ matrix.service }}
        file: ./src/${{ matrix.service }}/Dockerfile
        push: true
        tags: |
          ${{ env.REGISTRY }}/${{ github.repository }}/${{ matrix.service }}:${{ github.sha }}
          ${{ env.REGISTRY }}/${{ github.repository }}/${{ matrix.service }}:latest
```

---

## Test Pipeline

### Unit Tests

```yaml
name: Run Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-go:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service:
        - frontend
        - productcatalogservice
        - checkoutservice
        - shippingservice
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Go
      uses: actions/setup-go@v4
      with:
        go-version: '1.21'
    
    - name: Run tests for ${{ matrix.service }}
      run: |
        cd src/${{ matrix.service }}
        go test -v -race -coverprofile=coverage.out ./...
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./src/${{ matrix.service }}/coverage.out

  test-nodejs:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service:
        - currencyservice
        - paymentservice
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
    
    - name: Install dependencies for ${{ matrix.service }}
      run: |
        cd src/${{ matrix.service }}
        npm ci
    
    - name: Run tests
      run: |
        cd src/${{ matrix.service }}
        npm test -- --coverage

  test-python:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service:
        - emailservice
        - recommendationservice
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies for ${{ matrix.service }}
      run: |
        cd src/${{ matrix.service }}
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        cd src/${{ matrix.service }}
        pytest --cov --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Image Scanning

```yaml
name: Scan Images for Vulnerabilities

on:
  push:
    branches: [main]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Build image
      run: docker build -t app:${{ github.sha }} ./src/frontend
    
    - name: Run Trivy scan
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'app:${{ github.sha }}'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
```

---

## Deployment Pipeline

### Deploy to Development

```yaml
name: Deploy to Development

on:
  push:
    branches: [develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: development
      url: https://dev.boutique.example.com
    
    steps:
    - uses: actions/checkout@v4
    
    # Setup kubectl
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
      with:
        version: 'v1.27.0'
    
    # Setup kubeconfig
    - name: Configure kubectl
      run: |
        mkdir -p $HOME/.kube
        echo "${{ secrets.KUBE_CONFIG_DEV }}" | base64 -d > $HOME/.kube/config
        chmod 600 $HOME/.kube/config
    
    # Deploy using kubectl
    - name: Deploy to development cluster
      run: |
        kubectl apply -k kubernetes/overlays/dev
        kubectl rollout status deployment/frontend -n online-boutique
    
    # Verify deployment
    - name: Verify deployment
      run: |
        kubectl get pods -n online-boutique
        kubectl get svc -n online-boutique
    
    # Health check
    - name: Health check
      run: |
        for i in {1..30}; do
          STATUS=$(kubectl get svc frontend -n online-boutique -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
          if [ -n "$STATUS" ]; then
            curl -f https://dev.boutique.example.com/health && break
            sleep 5
          fi
        done
```

### Deploy to Production with Approval

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
    tags:
    - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://boutique.example.com
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
    
    - name: Configure kubectl
      run: |
        mkdir -p $HOME/.kube
        echo "${{ secrets.KUBE_CONFIG_PROD }}" | base64 -d > $HOME/.kube/config
        chmod 600 $HOME/.kube/config
    
    - name: Set image tag
      run: echo "IMAGE_TAG=${{ github.sha }}" >> $GITHUB_ENV
    
    # Update deployment manifests
    - name: Update deployment manifests
      run: |
        sed -i "s/:latest/:${{ env.IMAGE_TAG }}/g" kubernetes/overlays/production/deployment.yaml
    
    # Apply using Kustomize
    - name: Deploy to production
      run: |
        kubectl apply -k kubernetes/overlays/production
        kubectl rollout status deployment/frontend -n online-boutique --timeout=5m
    
    # Smoke tests
    - name: Run smoke tests
      run: |
        FRONTEND_IP=$(kubectl get svc frontend -n online-boutique -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        for i in {1..5}; do
          echo "Testing endpoint $i..."
          curl -f "http://$FRONTEND_IP/product?id=$i" || exit 1
        done
    
    # Rollback on failure
    - name: Rollback on failure
      if: failure()
      run: |
        kubectl rollout undo deployment/frontend -n online-boutique
        kubectl rollout status deployment/frontend -n online-boutique
        echo "Deployment rolled back due to failure"
        exit 1
    
    # Notify deployment
    - name: Notify deployment
      uses: 8398a7/action-slack@v3
      if: always()
      with:
        status: ${{ job.status }}
        text: 'Production deployment ${{ job.status }}'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## Complete Workflow

### Combined CI/CD Pipeline

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
    paths-ignore:
    - 'docs/**'
    - '*.md'
  pull_request:
    branches: [main, develop]

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ${{ github.repository }}

jobs:
  # TESTS
  test:
    name: Test (${{ matrix.language }})
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
        - language: go
          services: frontend,productcatalogservice,checkoutservice,shippingservice
        - language: nodejs
          services: currencyservice,paymentservice
        - language: python
          services: emailservice,recommendationservice
        - language: java
          services: adservice

    steps:
    - uses: actions/checkout@v4
    - name: Run tests
      run: echo "Running ${{ matrix.language }} tests"
    # Add actual test commands

  # BUILD
  build:
    name: Build Images
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push'
    
    strategy:
      matrix:
        service:
        - frontend
        - cartservice
        - productcatalogservice
        - currencyservice
        - paymentservice
        - shippingservice
        - emailservice
        - checkoutservice
        - recommendationservice
        - adservice
    
    steps:
    - uses: actions/checkout@v4
    
    - uses: docker/setup-buildx-action@v3
    
    - name: Log in to registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: ./src/${{ matrix.service }}
        push: true
        tags: |
          ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/${{ matrix.service }}:${{ github.sha }}
          ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/${{ matrix.service }}:latest
    
    - name: Image digest
      run: echo "Image digest: ${{ steps.docker_build.outputs.digest }}"

  # DEPLOY TO DEV
  deploy-dev:
    name: Deploy to Development
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment:
      name: development

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
    
    - name: Configure kubectl
      env:
        KUBECONFIG_CONTENT: ${{ secrets.KUBECONFIG_DEV }}
      run: |
        mkdir -p $HOME/.kube
        echo "$KUBECONFIG_CONTENT" | base64 -d > $HOME/.kube/config
    
    - name: Deploy
      run: kubectl apply -k kubernetes/overlays/dev

  # DEPLOY TO PROD
  deploy-prod:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
    
    - name: Configure kubectl
      env:
        KUBECONFIG_CONTENT: ${{ secrets.KUBECONFIG_PROD }}
      run: |
        mkdir -p $HOME/.kube
        echo "$KUBECONFIG_CONTENT" | base64 -d > $HOME/.kube/config
    
    - name: Deploy
      run: kubectl apply -k kubernetes/overlays/production
    
    - name: Verify rollout
      run: kubectl rollout status deployment/frontend -n online-boutique --timeout=5m
```

---

## Setting Up Secrets

In GitHub repository settings:

```
Settings → Secrets and variables → Actions → New repository secret

Required Secrets:
- GCP_SERVICE_ACCOUNT: (base64 encoded service account key)
- KUBECONFIG_DEV: (base64 encoded dev kubeconfig)
- KUBECONFIG_PROD: (base64 encoded prod kubeconfig)
- SLACK_WEBHOOK: (Slack webhook URL for notifications)

Optional:
- DOCKER_USERNAME: Docker Hub username
- DOCKER_PASSWORD: Docker Hub token
```

---

## Commands Summary

```bash
# View workflow runs
gh workflow list
gh run list --workflow=ci-cd.yml

# View job logs
gh run view <run-id>
gh run view <run-id> --log

# Manually trigger workflow
gh workflow run ci-cd.yml

# Cancel workflow
gh run cancel <run-id>

# View workflow status
gh run view <run-id> --json status
```

---

**Next:** See [05-TERRAFORM.md](05-TERRAFORM.md) to learn about infrastructure as code!
