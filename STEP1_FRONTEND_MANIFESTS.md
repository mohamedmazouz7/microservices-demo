# Step 1: Understanding Your First Kubernetes Manifests

You now have **actual microservice code** in your repo and **three Kubernetes manifest files** for the frontend service. Let's understand what each does.

## 📁 What You Have

```
/home/nirou/K8s/microservices/microservices-demo/
├── src/                          # Actual microservice code
│   ├── frontend/                 # Frontend service (Go)
│   ├── cartservice/              # Cart service (C#)
│   ├── productcatalogservice/    # Product service (Go)
│   └── ... (8 more services)
└── k8s/                          # Kubernetes manifests
    ├── frontend-deployment.yaml  # How to run frontend Pods
    ├── frontend-service.yaml     # How to expose frontend
    └── frontend-configmap.yaml   # Frontend configuration
```

## 🎯 The Three Files Explained

### 1. **Deployment** (`frontend-deployment.yaml`)
**What it does:** Tells Kubernetes to run copies of your frontend container

**Key concepts:**
- **Replicas: 2** → "Keep 2 copies running"
- **Selector** → "Which Pods do I manage?" (answer: ones with label `app: frontend`)
- **Container image** → "Use `gcr.io/google-samples/microservices-demo/frontend:v0.3.9`"
- **Port 8080** → Where the app listens inside the container
- **Resources** → CPU/memory limits (so it doesn't crash your cluster)
- **Probes** → Health checks (readiness = ready to serve, liveness = still alive?)

### 2. **Service** (`frontend-service.yaml`)
**What it does:** Creates a stable DNS name and load balancer for Pods

**Key concepts:**
- **Type: LoadBalancer** → Create external access (on cloud, creates real load balancer; locally, just NodePort)
- **Port 80** → External port (clients connect here)
- **TargetPort 8080** → Internal port (Pods listen here)
- **Selector: app: frontend** → "Route traffic to Pods with label app: frontend"
- **DNS name** → Automatically created: `frontend.default.svc.cluster.local`

### 3. **ConfigMap** (`frontend-configmap.yaml`)
**What it does:** Stores configuration data separately from the container

**Key concepts:**
- **Environment variables** → Endpoints of other services (cart, catalog, etc.)
- **Why separate?** → Same container image works anywhere; just change ConfigMap values
- **How to use** → Deployment references ConfigMap to inject environment variables

## 🚀 How It All Works Together

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Kubernetes Cluster                   │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Frontend Service (LoadBalancer)                        │ │
│  │ - External IP: 192.168.1.100 (or cloud LB)           │ │
│  │ - Port: 80                                             │ │
│  │ - DNS: frontend.default.svc.cluster.local             │ │
│  │ - Routes to: Pods with label app: frontend            │ │
│  └─────────┬──────────────────────────┬───────────────────┘ │
│            │                          │                      │
│      ┌─────▼──────┐           ┌──────▼────────┐            │
│      │   Pod 1    │           │    Pod 2      │            │
│      │ Frontend   │           │  Frontend     │            │
│      │ Port 8080  │           │  Port 8080    │            │
│      │ Config:   │           │  Config:      │            │
│      │ -PRODUCT_ │           │  -PRODUCT_    │            │
│      │ CATALOG.. │           │  CATALOG..    │            │
│      └───────────┘           └───────────────┘            │
│                                                               │
│  ConfigMap (frontend-config): Stores env vars for both Pods  │
└─────────────────────────────────────────────────────────────┘

Client connects to: frontend.default.svc.cluster.local:80
Service load-balances between Pod 1 and Pod 2
Both Pods use same config from ConfigMap
```

## 🔄 Step-by-Step: What Happens

1. **You apply the Deployment:**
   ```bash
   kubectl apply -f frontend-deployment.yaml
   ```
   Kubernetes creates:
   - Pod 1 (with your container image)
   - Pod 2 (backup copy)

2. **You apply the Service:**
   ```bash
   kubectl apply -f frontend-service.yaml
   ```
   Kubernetes creates:
   - Internal DNS: `frontend.default.svc.cluster.local`
   - External load balancer (points to both Pods)

3. **You apply the ConfigMap:**
   ```bash
   kubectl apply -f frontend-configmap.yaml
   ```
   Kubernetes stores the configuration (Pods don't auto-reload though)

4. **When Pod 1 crashes:**
   - Deployment notices Pod 1 is gone
   - Deployment spins up a new Pod 1
   - Service automatically updates (new Pod 1 IP added to endpoint list)
   - Clients see no disruption (service still working)

5. **When you scale:**
   ```bash
   kubectl scale deployment frontend --replicas=5
   ```
   - Kubernetes creates 3 more Pods
   - Service automatically finds them (same label matching)
   - Traffic automatically distributes across 5 Pods

## 📚 Key Kubernetes Concepts in These Files

| Concept | Explanation | Example |
|---------|-------------|---------|
| **Pod** | Smallest Kubernetes unit; usually runs 1 container | Frontend Pod |
| **Deployment** | Manages Pods; ensures N replicas always running | "Keep 2 frontend Pods running" |
| **Service** | Network abstraction; load balancer + DNS | "Route traffic to frontend Pods" |
| **ConfigMap** | Non-secret configuration storage | Service endpoints, log levels |
| **Label** | Key-value tag for organizing objects | `app: frontend`, `version: v1` |
| **Selector** | Way to find objects by labels | `app: frontend` |

## ⚙️ Next Steps

Now you'll learn by doing. You have two choices:

### Option A: Understand ConfigMap Better (Recommended First)
Open `frontend-deployment.yaml` and modify the `env:` section to use the ConfigMap:

```yaml
env:
- name: PRODUCT_CATALOG_SERVICE_ADDR
  valueFrom:
    configMapKeyRef:
      name: frontend-config
      key: PRODUCT_CATALOG_SERVICE_ADDR
```

This injects the config values into the container as environment variables.

### Option B: Deploy This Locally
If you have `kubectl` and a local cluster (Minikube, Docker Desktop, Kind):

```bash
cd /home/nirou/K8s/microservices/microservices-demo

# Apply all three files
kubectl apply -f k8s/frontend-configmap.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml

# Check if Pods are running
kubectl get pods

# Check the service
kubectl get svc

# View logs from a Pod
kubectl logs -f deployment/frontend
```

## 🎓 Learning Path

You now understand:
- ✅ What Deployment does
- ✅ What Service does
- ✅ What ConfigMap does
- ✅ How labels and selectors connect them
- ✅ How health checks work

**Next:** You'll write these manifests yourself for another service (cartservice or productcatalogservice) to reinforce the concepts.

---

**Remember:** The goal is not to memorize YAML syntax, but to understand the *why* behind each field.
