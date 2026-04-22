# Kubernetes Deployment & Orchestration Guide

## 📚 Table of Contents

1. [Kubernetes Fundamentals](#kubernetes-fundamentals)
2. [Core Resources](#core-resources)
3. [Deployment Manifest](#deployment-manifest)
4. [Services & Networking](#services--networking)
5. [Configuration Management](#configuration-management)
6. [StatefulSets for Databases](#statefulsets-for-databases)
7. [Advanced Patterns](#advanced-patterns)

---

## Kubernetes Fundamentals

### What is Kubernetes?

**Container Orchestration Platform** that:
- ✅ Automates deployment and scaling
- ✅ Manages container lifecycle
- ✅ Provides high availability
- ✅ Enables rolling updates with zero downtime
- ✅ Handles resource allocation and scheduling
- ✅ Provides networking and storage abstraction

### Kubernetes Cluster Architecture

```
┌─────────────────────────── Kubernetes Cluster ──────────────────────────┐
│                                                                          │
│  ┌──────────────── Control Plane (Master) ──────────────┐             │
│  │  ┌──────────────────────────────────────────────┐    │             │
│  │  │  API Server: REST API for all operations    │    │             │
│  │  │  (kubectl talks to this)                    │    │             │
│  │  └──────────────────────────────────────────────┘    │             │
│  │                                                       │             │
│  │  ┌──────────────────────────────────────────────┐    │             │
│  │  │ etcd: Distributed key-value store           │    │             │
│  │  │ Stores all cluster state and config         │    │             │
│  │  └──────────────────────────────────────────────┘    │             │
│  │                                                       │             │
│  │  ┌──────────────────────────────────────────────┐    │             │
│  │  │ Scheduler: Assigns pods to nodes            │    │             │
│  │  └──────────────────────────────────────────────┘    │             │
│  │                                                       │             │
│  │  ┌──────────────────────────────────────────────┐    │             │
│  │  │ Controller Manager: Ensures desired state   │    │             │
│  │  └──────────────────────────────────────────────┘    │             │
│  └──────────────────────────────────────────────────────┘             │
│                                                                          │
│  ┌─────── Worker Node 1 ─────┐  ┌─────── Worker Node 2 ─────┐        │
│  │  ┌─────────────────────┐   │  │  ┌─────────────────────┐   │        │
│  │  │ kubelet             │   │  │  │ kubelet             │   │        │
│  │  │ (Container manager) │   │  │  │ (Container manager) │   │        │
│  │  └─────────────────────┘   │  │  └─────────────────────┘   │        │
│  │  ┌─────────────────────┐   │  │  ┌─────────────────────┐   │        │
│  │  │ kube-proxy          │   │  │  │ kube-proxy          │   │        │
│  │  │ (Networking)        │   │  │  │ (Networking)        │   │        │
│  │  └─────────────────────┘   │  │  └─────────────────────┘   │        │
│  │  ┌─────────────────────┐   │  │  ┌─────────────────────┐   │        │
│  │  │ Container Runtime   │   │  │  │ Container Runtime   │   │        │
│  │  │ (Docker, containerd)│   │  │  │ (Docker, containerd)│   │        │
│  │  └─────────────────────┘   │  │  └─────────────────────┘   │        │
│  │         ┌───────────┐      │  │         ┌───────────┐      │        │
│  │         │ Pod       │      │  │         │ Pod       │      │        │
│  │         │ container │      │  │         │ container │      │        │
│  │         └───────────┘      │  │         └───────────┘      │        │
│  └──────────────────────────────┘  └──────────────────────────┘        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Pod: The Smallest Unit

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: frontend-pod
spec:
  containers:
  - name: frontend
    image: gcr.io/project/frontend:1.0
    ports:
    - containerPort: 8080
```

**Important:** Pods are ephemeral (temporary). They can be created and destroyed anytime. Rarely deploy Pods directly!

---

## Core Resources

### 1. Deployment (Most Common)

**Purpose:** Manage stateless applications with desired replicas

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  labels:
    app: frontend
  namespace: default
spec:
  # How many replicas (Pod copies) to maintain
  replicas: 3
  
  # Pod selector - must match template.metadata.labels
  selector:
    matchLabels:
      app: frontend
  
  # Rolling update strategy
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1           # Max additional Pods during update
      maxUnavailable: 0     # Min available Pods during update
  
  # Pod template
  template:
    metadata:
      labels:
        app: frontend
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
    spec:
      # Pod level security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      
      # Service account for RBAC
      serviceAccountName: frontend
      
      containers:
      - name: frontend
        image: gcr.io/project/frontend:1.0
        imagePullPolicy: IfNotPresent
        
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
        
        # Container level security
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        
        # Environment variables
        env:
        - name: PORT
          value: "8080"
        - name: PRODUCT_CATALOG_ADDR
          value: "productcatalog:3550"
        
        # From ConfigMap
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: log_level
        
        # From Secret
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: password
        
        # Liveness Probe (restart if unhealthy)
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        # Readiness Probe (remove from LB if not ready)
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        
        # Startup Probe (wait for app to start)
        startupProbe:
          httpGet:
            path: /health
            port: 8080
          failureThreshold: 30
          periodSeconds: 10
        
        # Resource requests and limits
        resources:
          requests:
            cpu: 100m          # Minimum CPU
            memory: 128Mi      # Minimum memory
          limits:
            cpu: 500m          # Maximum CPU
            memory: 512Mi      # Maximum memory
        
        # Volume mounts
        volumeMounts:
        - name: config
          mountPath: /etc/config
          readOnly: true
        - name: cache
          mountPath: /tmp/cache
      
      # Pod-level volumes
      volumes:
      - name: config
        configMap:
          name: app-config
      - name: cache
        emptyDir: {}
      
      # Restart policy
      restartPolicy: Always
      
      # Termination grace period
      terminationGracePeriodSeconds: 30
      
      # Affinity rules
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - frontend
              topologyKey: kubernetes.io/hostname
```

**Commands:**
```bash
kubectl apply -f deployment.yaml          # Create
kubectl get deployments                   # List
kubectl describe deployment frontend      # Details
kubectl scale deployment frontend --replicas=5  # Scale
kubectl set image deployment/frontend frontend=gcr.io/project/frontend:2.0  # Update image
kubectl rollout status deployment/frontend      # Track rollout
kubectl rollout undo deployment/frontend        # Rollback
kubectl delete deployment frontend        # Delete
```

### 2. Service (Networking)

**Purpose:** Stable IP and DNS for accessing Pods

```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend
  labels:
    app: frontend
spec:
  # Service type
  type: LoadBalancer  # or ClusterIP, NodePort
  
  # Pod selector - must match deployment labels
  selector:
    app: frontend
  
  # Ports configuration
  ports:
  - name: http
    protocol: TCP
    port: 80           # Service port
    targetPort: 8080   # Container port
    nodePort: 30080    # (NodePort only)
  
  # Session affinity
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600
```

**Service Types:**

```
1. ClusterIP (default)
   ┌─────────────────────────────┐
   │    Internal Kubernetes      │
   │         Network             │
   │                             │
   │ frontend:80 (DNS)  →  Pod   │
   │                             │
   │ (No external access)        │
   └─────────────────────────────┘

2. NodePort
   ┌─────────────────────────────┐
   │        External Users       │
   │            │                │
   │            ↓                │
   │      Node:30080 (NodePort)  │
   │            │                │
   │            ↓                │
   │      frontend:80 (service)  │
   │            │                │
   │            ↓                │
   │           Pod              │
   └─────────────────────────────┘

3. LoadBalancer
   ┌─────────────────────────────┐
   │    External Load Balancer   │
   │   (Cloud provider manages)  │
   │            │                │
   │            ↓                │
   │      Node:30080 (NodePort)  │
   │            │                │
   │            ↓                │
   │      frontend:80 (service)  │
   │            │                │
   │            ↓                │
   │    Pod1, Pod2, Pod3         │
   └─────────────────────────────┘
```

**Commands:**
```bash
kubectl apply -f service.yaml              # Create
kubectl get services                       # List
kubectl describe service frontend          # Details
kubectl port-forward svc/frontend 8080:80  # Local access
kubectl delete service frontend            # Delete
```

### 3. ConfigMap (Configuration)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  # Simple key-value
  LOG_LEVEL: "info"
  DATABASE_HOST: "postgres.default.svc.cluster.local"
  
  # Multi-line configuration
  app.conf: |
    server:
      port: 8080
      timeout: 30s
    database:
      pool_size: 10
```

**Usage:**

```yaml
# As environment variables
env:
- name: LOG_LEVEL
  valueFrom:
    configMapKeyRef:
      name: app-config
      key: LOG_LEVEL

# As volume mount
volumeMounts:
- name: config
  mountPath: /etc/config

volumes:
- name: config
  configMap:
    name: app-config
```

**Commands:**
```bash
kubectl create configmap app-config --from-literal=LOG_LEVEL=info
kubectl get configmaps
kubectl describe configmap app-config
kubectl edit configmap app-config  # Edit in place
```

### 4. Secret (Sensitive Data)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque  # Generic binary secret
data:
  # Values MUST be base64 encoded
  password: cGFzc3dvcmQxMjM=  # base64("password123")
  api_key: c2VjcmV0a2V5
```

**Create Secret:**
```bash
# From literals
kubectl create secret generic db-secret \
  --from-literal=password=password123 \
  --from-literal=username=admin

# From files
kubectl create secret generic db-secret \
  --from-file=cert.crt \
  --from-file=cert.key

# Docker registry secret (for private images)
kubectl create secret docker-registry regcred \
  --docker-server=gcr.io \
  --docker-username=json_key \
  --docker-password="$(cat keyfile.json)"

# TLS secret
kubectl create secret tls tls-secret \
  --cert=path/to/cert \
  --key=path/to/key
```

**Usage in Pod:**
```yaml
containers:
- name: app
  env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-secret
        key: password
  
  volumeMounts:
  - name: tls
    mountPath: /etc/tls

volumes:
- name: tls
  secret:
    secretName: tls-secret
```

### 5. Namespace (Logical Separation)

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
```

**Commands:**
```bash
kubectl create namespace production
kubectl get namespaces
kubectl apply -f manifest.yaml -n production
kubectl delete namespace production
```

---

## Deployment Manifest

### Complete Example

```yaml
---
# Namespace
apiVersion: v1
kind: Namespace
metadata:
  name: online-boutique

---
# ConfigMap for environment variables
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: online-boutique
data:
  PRODUCT_CATALOG_ADDR: productcatalog:3550
  CART_ADDR: cartservice:7070
  LOG_LEVEL: info

---
# Secret for sensitive data
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
  namespace: online-boutique
type: Opaque
data:
  password: dGVzdHBhc3N3b3Jk  # "testpasswd"

---
# ServiceAccount for RBAC
apiVersion: v1
kind: ServiceAccount
metadata:
  name: frontend
  namespace: online-boutique

---
# Service for networking
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: online-boutique
spec:
  type: LoadBalancer
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 8080

---
# Deployment for application
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: online-boutique
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
      serviceAccountName: frontend
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      
      containers:
      - name: frontend
        image: gcr.io/project/frontend:1.0
        ports:
        - containerPort: 8080
        
        envFrom:
        - configMapRef:
            name: app-config
        
        env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: password
        
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          periodSeconds: 10
        
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          periodSeconds: 5
        
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
```

---

## Services & Networking

### Service Discovery

**Within Cluster:**
```
podname.namespace.svc.cluster.local

Examples:
- frontend.default.svc.cluster.local
- productcatalog.online-boutique.svc.cluster.local
- redis.default.svc.cluster.local

DNS automatically resolves to Service IP
```

**DNS Round-Robin:**
```yaml
# Service acts as load balancer
Service IP → Pod1 (IP: 10.0.1.1)
          → Pod2 (IP: 10.0.1.2)
          → Pod3 (IP: 10.0.1.3)

Each request distributed randomly
```

### Ingress (External Access)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: frontend-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - boutique.example.com
    secretName: tls-boutique
  
  rules:
  - host: boutique.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

---

## Configuration Management

### Kustomize (Environment-specific configs)

**Base Configuration:**
```yaml
# kubernetes/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: online-boutique

commonLabels:
  app.kubernetes.io/managed-by: kustomize

resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml
```

**Dev Overlay:**
```yaml
# kubernetes/overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
  - ../../base

replicas:
- name: frontend
  count: 1

patchesJson6902:
- target:
    group: apps
    version: v1
    kind: Deployment
    name: frontend
  patch: |-
    - op: replace
      path: /spec/template/spec/containers/0/image
      value: frontend:dev
    - op: replace
      path: /spec/template/spec/containers/0/resources/limits/memory
      value: 256Mi
```

**Production Overlay:**
```yaml
# kubernetes/overlays/production/kustomization.yaml
replicas:
- name: frontend
  count: 5

patchesJson6902:
- target:
    group: apps
    version: v1
    kind: Deployment
    name: frontend
  patch: |-
    - op: replace
      path: /spec/template/spec/containers/0/image
      value: frontend:1.0
    - op: replace
      path: /spec/template/spec/containers/0/resources/limits
      value:
        cpu: "1"
        memory: "512Mi"
```

**Deploy:**
```bash
kubectl apply -k kubernetes/overlays/dev
kubectl apply -k kubernetes/overlays/production
```

---

## StatefulSets for Databases

For applications that need stable identities (databases, message queues):

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
          name: postgres
        
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  
  # Persistent Volume Claims
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes:
      - ReadWriteOnce
      resources:
        requests:
          storage: 10Gi
```

**Key Differences from Deployment:**
- **Stable Network Identity:** postgres-0, postgres-1, postgres-2
- **Persistent Storage:** Each pod gets its own PVC
- **Ordered Creation/Deletion:** Sequential startup/shutdown
- **Sticky Identity:** Same pod, same storage across recreations

---

## Advanced Patterns

### Horizontal Pod Autoscaler (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: frontend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: frontend
  
  minReplicas: 2
  maxReplicas: 10
  
  metrics:
  # CPU-based scaling
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  
  # Memory-based scaling
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  
  # Custom metrics
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: 1000
  
  # Scale up behavior
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 100  # Double the pods
        periodSeconds: 15
    
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50   # Remove 50% of pods
        periodSeconds: 15
```

**Commands:**
```bash
kubectl autoscale deployment frontend --min=2 --max=10 --cpu-percent=70
kubectl get hpa
kubectl describe hpa frontend-hpa
kubectl delete hpa frontend-hpa
```

### Pod Disruption Budgets (PDB)

Ensure minimum availability during node maintenance:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: frontend-pdb
spec:
  minAvailable: 2  # Or use maxUnavailable: 1
  selector:
    matchLabels:
      app: frontend
```

---

## Hands-On Exercise

### Deploy Online Boutique Frontend

**Step 1: Create namespace**
```bash
kubectl create namespace online-boutique
```

**Step 2: Create ConfigMap**
```bash
kubectl create configmap frontend-config \
  --from-literal=PRODUCT_CATALOG_ADDR=productcatalog:3550 \
  -n online-boutique
```

**Step 3: Create and apply Deployment**
```yaml
# frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: online-boutique
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
      - name: frontend
        image: gcr.io/project/frontend:1.0
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: frontend-config
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          periodSeconds: 5
```

**Step 4: Create Service**
```yaml
# frontend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: online-boutique
spec:
  type: LoadBalancer
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 8080
```

**Step 5: Apply manifests**
```bash
kubectl apply -f frontend-deployment.yaml
kubectl apply -f frontend-service.yaml
```

**Step 6: Verify**
```bash
kubectl get pods -n online-boutique
kubectl get services -n online-boutique
kubectl logs -f deployment/frontend -n online-boutique
```

**Step 7: Access application**
```bash
# If using LoadBalancer (cloud)
kubectl get service frontend -n online-boutique
# Get EXTERNAL-IP

# If using local cluster (Minikube, Kind)
kubectl port-forward svc/frontend 8080:80 -n online-boutique
# Visit http://localhost:8080
```

---

## Summary

| Resource | Purpose | Use Case |
|----------|---------|----------|
| Pod | Smallest deployable unit | Rarely used directly |
| Deployment | Manage replicated pods | Stateless applications |
| Service | Network abstraction | Pod discovery & load balancing |
| ConfigMap | Non-sensitive config | Environment variables, configs |
| Secret | Sensitive data | Passwords, API keys, certs |
| StatefulSet | Stateful applications | Databases, message queues |
| HPA | Auto-scaling | Handle traffic spikes |
| Ingress | External HTTP/HTTPS | Domain-based routing |
| Namespace | Logical separation | Multi-tenancy, RBAC |
| PDB | Disruption protection | Maintain availability |

---

**Next:** See [03-HELM.md](03-HELM.md) to learn about package management!
