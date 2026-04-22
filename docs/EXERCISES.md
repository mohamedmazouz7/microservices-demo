# Practical Exercises - Hands-On Learning

This guide contains practical exercises to reinforce your learning. Follow them in order for best results.

## Exercise 1: Docker Basics (30 minutes)

### Goal
Create a Docker image and run a container locally.

### Steps

**1.1 Create a simple Go application**

Create `hello-app/main.go`:
```go
package main

import (
    "fmt"
    "log"
    "net/http"
)

func main() {
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "Hello, World!")
    })
    
    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
    })
    
    log.Println("Server starting on :8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

**1.2 Write a Dockerfile**

Create `hello-app/Dockerfile`:
```dockerfile
FROM golang:1.21 AS builder
WORKDIR /app
COPY main.go .
RUN go build -o app main.go

FROM alpine:3.19
RUN apk add --no-cache ca-certificates
WORKDIR /app
COPY --from=builder /app/app .
USER nobody
EXPOSE 8080
HEALTHCHECK CMD wget -q -O- http://localhost:8080/health || exit 1
CMD ["./app"]
```

**1.3 Build the image**

```bash
cd hello-app
docker build -t hello-app:1.0 .
```

**1.4 Run the container**

```bash
docker run -p 8080:8080 hello-app:1.0
```

**1.5 Test it**

```bash
# In another terminal
curl http://localhost:8080
# Should output: Hello, World!

# Check health
curl http://localhost:8080/health
```

✅ **Exercise Complete!** You've:
- Written a Go app
- Created a multi-stage Dockerfile
- Built and ran a container
- Tested the running application

---

## Exercise 2: Docker Compose (30 minutes)

### Goal
Run multiple services locally with Docker Compose.

### Steps

**2.1 Create docker-compose.yml**

```yaml
version: '3.8'

services:
  app:
    build:
      context: ./hello-app
      dockerfile: Dockerfile
    container_name: hello-app
    ports:
      - "8080:8080"
    environment:
      - LOG_LEVEL=info
    depends_on:
      - redis
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "wget", "-q", "-O-", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    networks:
      - app-network
    volumes:
      - redis-data:/data

networks:
  app-network:
    driver: bridge

volumes:
  redis-data:
```

**2.2 Start services**

```bash
docker-compose up -d
```

**2.3 Check services**

```bash
# List running services
docker-compose ps

# View logs
docker-compose logs -f app

# Check if app can reach Redis
docker-compose exec app ping redis
```

**2.4 Test the application**

```bash
curl http://localhost:8080
```

**2.5 Stop services**

```bash
docker-compose down
```

✅ **Exercise Complete!** You've:
- Orchestrated multiple containers
- Managed networking between services
- Used volumes for data persistence
- Viewed logs and monitored health

---

## Exercise 3: Kubernetes Deployment (45 minutes)

### Goal
Deploy the application to a local Kubernetes cluster.

### Steps

**3.1 Start Minikube**

```bash
minikube start --cpus=4 --memory=4096
```

**3.2 Enable the Docker registry**

```bash
eval $(minikube docker-env)
cd hello-app
docker build -t hello-app:k8s .
cd ..
```

**3.3 Create Kubernetes manifests**

Create `k8s/namespace.yaml`:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: learning
```

Create `k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello-app
  namespace: learning
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hello-app
  template:
    metadata:
      labels:
        app: hello-app
    spec:
      containers:
      - name: app
        image: hello-app:k8s
        imagePullPolicy: Never  # Use local image in Minikube
        ports:
        - containerPort: 8080
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            cpu: 100m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 128Mi
```

Create `k8s/service.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: hello-app
  namespace: learning
spec:
  type: LoadBalancer
  selector:
    app: hello-app
  ports:
  - port: 8080
    targetPort: 8080
```

**3.4 Deploy to Kubernetes**

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create deployment and service
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

**3.5 Verify deployment**

```bash
# Check pods
kubectl get pods -n learning

# Check services
kubectl get svc -n learning

# View pod details
kubectl describe pod <pod-name> -n learning

# View logs
kubectl logs deployment/hello-app -n learning -f
```

**3.6 Access the application**

```bash
# Port forward
kubectl port-forward svc/hello-app 8080:8080 -n learning

# In another terminal, test
curl http://localhost:8080
```

**3.7 Try scaling**

```bash
# Scale to 5 replicas
kubectl scale deployment hello-app --replicas=5 -n learning

# Watch pods
kubectl get pods -n learning -w

# View distribution
kubectl get pods -n learning -o wide
```

**3.8 Update the deployment**

```bash
# Edit deployment to add label
kubectl set env deployment/hello-app VERSION=2.0 -n learning

# Watch rollout
kubectl rollout status deployment/hello-app -n learning

# Rollback if needed
kubectl rollout undo deployment/hello-app -n learning
```

✅ **Exercise Complete!** You've:
- Deployed to a real Kubernetes cluster
- Used Deployments and Services
- Implemented health checks
- Scaled the application
- Performed rolling updates

---

## Exercise 4: Kustomize (30 minutes)

### Goal
Use Kustomize for environment-specific configurations.

### Steps

**4.1 Create directory structure**

```bash
mkdir -p kustomize/base kustomize/overlays/{dev,prod}
```

**4.2 Create base configuration**

`kustomize/base/kustomization.yaml`:
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: learning

resources:
  - deployment.yaml
  - service.yaml

commonLabels:
  app: hello-app
  managed-by: kustomize
```

Copy your `deployment.yaml` and `service.yaml` to `kustomize/base/`

**4.3 Create dev overlay**

`kustomize/overlays/dev/kustomization.yaml`:
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
  - ../../base

namePrefix: dev-

patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
      name: dev-hello-app
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 1
```

**4.4 Create prod overlay**

`kustomize/overlays/prod/kustomization.yaml`:
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
  - ../../base

namePrefix: prod-

patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
      name: prod-hello-app
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 3
```

**4.5 Deploy with Kustomize**

```bash
# Deploy dev
kubectl apply -k kustomize/overlays/dev

# Deploy prod
kubectl apply -k kustomize/overlays/prod

# Check namespaces
kubectl get deployments -A
```

✅ **Exercise Complete!** You've:
- Organized configurations with Kustomize
- Created reusable base configurations
- Built environment-specific overlays
- Deployed different configurations

---

## Exercise 5: ConfigMap & Secrets (30 minutes)

### Goal
Manage configuration and secrets in Kubernetes.

### Steps

**5.1 Create ConfigMap**

```bash
kubectl create configmap app-config \
  --from-literal=APP_NAME=hello-app \
  --from-literal=VERSION=1.0 \
  --from-literal=LOG_LEVEL=info \
  -n learning
```

**5.2 Create Secret**

```bash
kubectl create secret generic app-secret \
  --from-literal=SECRET_KEY=my-secret-value \
  -n learning
```

**5.3 Update Deployment to use ConfigMap and Secret**

```yaml
spec:
  template:
    spec:
      containers:
      - name: app
        envFrom:
        - configMapRef:
            name: app-config
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secret
              key: SECRET_KEY
```

**5.4 Verify environment variables**

```bash
# Get pod name
POD=$(kubectl get pod -n learning -l app=hello-app -o jsonpath='{.items[0].metadata.name}')

# Check environment
kubectl exec -it $POD -n learning -- env | grep -E "APP_NAME|VERSION|LOG_LEVEL|SECRET_KEY"
```

✅ **Exercise Complete!** You've:
- Created ConfigMaps for configuration
- Created Secrets for sensitive data
- Injected them into pods
- Verified the values

---

## Exercise 6: Probes & Restarts (30 minutes)

### Goal
Understand Kubernetes health checks and self-healing.

### Steps

**6.1 Delete a pod**

```bash
# Get pod name
kubectl get pods -n learning

# Delete one pod
kubectl delete pod <pod-name> -n learning

# Watch Kubernetes recreate it
kubectl get pods -n learning -w
```

**6.2 Simulate unhealthy pod**

Update your Go app to have an endpoint that fails:

```go
var healthy = true

http.HandleFunc("/toggle-health", func(w http.ResponseWriter, r *http.Request) {
    healthy = !healthy
    fmt.Fprintf(w, "Health: %v", healthy)
})

http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
    if !healthy {
        w.WriteHeader(http.StatusInternalServerError)
        return
    }
    w.WriteHeader(http.StatusOK)
})
```

**6.3 Trigger unhealthiness**

```bash
# Get port-forward
kubectl port-forward svc/hello-app 8080:8080 -n learning

# In another terminal, make pod unhealthy
curl http://localhost:8080/toggle-health

# Watch pod restart
kubectl get pods -n learning -w
```

✅ **Exercise Complete!** You've:
- Triggered pod failures
- Watched Kubernetes self-heal
- Verified liveness probes
- Observed automatic restarts

---

## Exercise 7: Autoscaling (30 minutes)

### Goal
Set up Horizontal Pod Autoscaling based on CPU.

### Steps

**7.1 Create HPA**

```bash
kubectl autoscale deployment hello-app \
  --min=1 \
  --max=5 \
  --cpu-percent=30 \
  -n learning
```

**7.2 Generate load**

```bash
# Open new terminal, install wrk (load testing tool)
brew install wrk  # or apt-get install wrk

# Generate load
wrk -t4 -c100 -d60s http://localhost:8080
```

**7.3 Watch scaling**

```bash
# In another terminal, watch HPA
kubectl get hpa hello-app -n learning -w

# Watch pods
kubectl get pods -n learning -w
```

✅ **Exercise Complete!** You've:
- Created an HPA
- Generated load
- Watched automatic scaling
- Verified resource-based scaling

---

## Exercise 8: Helm Charts (Optional, 45 minutes)

### Goal
Package your application as a Helm chart.

### Steps

**8.1 Create Helm chart**

```bash
helm create charts/hello-app
cd charts/hello-app
```

**8.2 Update values.yaml**

```yaml
replicaCount: 3

image:
  repository: hello-app
  tag: "k8s"

service:
  type: LoadBalancer
  port: 8080

resources:
  limits:
    cpu: 200m
    memory: 128Mi
  requests:
    cpu: 100m
    memory: 64Mi
```

**8.3 Deploy with Helm**

```bash
helm install hello charts/hello-app -n learning
```

**8.4 Verify**

```bash
helm list -n learning
kubectl get all -n learning
```

✅ **Exercise Complete!** You've:
- Created a Helm chart
- Templated configurations
- Deployed with Helm
- Managed the application

---

## Summary

After completing these exercises, you should be comfortable with:

- ✅ Docker: Building images, using Dockerfile best practices
- ✅ Docker Compose: Multi-service local development
- ✅ Kubernetes: Deployments, Services, manifests
- ✅ Kustomize: Managing multiple environments
- ✅ ConfigMaps & Secrets: Configuration management
- ✅ Health Checks: Self-healing systems
- ✅ Autoscaling: Performance optimization
- ✅ Helm: Package management

---

## Challenge Projects

Ready for more? Try these:

1. **Deploy PostgreSQL to Kubernetes**
   - Use StatefulSets
   - Create persistent volumes
   - Use Secrets for credentials

2. **Set up Monitoring**
   - Install Prometheus
   - Create Grafana dashboards
   - Visualize metrics

3. **Implement Ingress**
   - Install Nginx Ingress Controller
   - Route traffic to multiple services
   - Add TLS certificates

4. **Deploy Real Microservices**
   - Deploy frontend service
   - Deploy backend service
   - Implement gRPC communication

5. **Set up CI/CD**
   - Create GitHub Actions workflow
   - Automated building and testing
   - Automated deployment

---

Happy Learning! 🚀
