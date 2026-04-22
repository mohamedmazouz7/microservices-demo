# Architecture Overview - Online Boutique Microservices

## 📊 System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Internet / Users                             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  Load Balancer  │ (Entry point)
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │   Ingress       │ (HTTP routing)
                        └────────┬────────┘
                                 │
                        ┌────────▼────────────────────┐
                        │    Frontend Service         │
                        │   (Go HTTP Server)          │
                        │   Serves web UI             │
                        └────────┬────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
    ┌───────▼─────┐    ┌────────▼────────┐   ┌──────▼──────┐
    │ProductService│    │  CartService    │   │AdService    │
    │ (Go)        │    │  (C#)           │   │ (Java)      │
    │ Port: 3550  │    │  Port: 7070     │   │ Port: 9555  │
    └─────────────┘    └────────┬────────┘   └─────────────┘
                                 │
                           ┌─────▼─────┐
                           │ Redis     │ (Session/Cart storage)
                           │ Port: 6379│
                           └───────────┘

            For each checkout:
            ┌────────────────────────────────────────────┐
            │     CheckoutService (Go, Port: 5050)      │
            │  Orchestrates: Payment, Shipping, Email   │
            ├────────────────────────────────────────────┤
            │  ├─ PaymentService (Node.js, 5000)       │
            │  ├─ ShippingService (Go, 50051)          │
            │  ├─ EmailService (Python, 8080)          │
            │  └─ CurrencyService (Node.js, 7000)      │
            └────────────────────────────────────────────┘

            Recommendations & Load Testing:
            ├─ RecommendationService (Python, 8080)
            └─ LoadGenerator (Python/Locust, 8089)
```

## 🔧 Microservices Breakdown

### 1. Frontend Service
**Language:** Go  
**Port:** 8080 (HTTP)  
**Responsibility:** 
- Serves the web UI
- Routes user requests to appropriate services
- Session management

**Key Technologies:**
- HTTP/REST for user interaction
- gRPC for backend communication
- HTML/CSS/JavaScript for UI

**Communication:**
```
User → Frontend (HTTP) → ProductService (gRPC)
                      → CartService (gRPC)
                      → CheckoutService (gRPC)
```

### 2. Product Catalog Service
**Language:** Go  
**Port:** 3550 (gRPC)  
**Responsibility:**
- Maintains product database
- Provides product listings
- Search functionality

**Data Flow:**
```
Frontend requests product list
    ↓
ProductCatalogService queries local JSON/database
    ↓
Returns product details to Frontend
```

### 3. Cart Service
**Language:** C#  
**Port:** 7070 (gRPC)  
**Responsibility:**
- Stores shopping cart items in Redis
- Adds/removes items
- Retrieves cart

**State Management:**
```
User Session ID
    ↓ (stored as key)
Redis → { item1, item2, ... } (cart contents)
```

### 4. Checkout Service
**Language:** Go  
**Port:** 5050 (gRPC)  
**Responsibility:**
- Orchestrates entire checkout process
- Coordinates with Payment, Shipping, Email services
- Transaction management

**Workflow:**
```
1. Retrieve cart from CartService
2. Calculate total with CurrencyService
3. Process payment with PaymentService
4. Calculate shipping with ShippingService
5. Send confirmation email with EmailService
6. Return order confirmation
```

### 5. Payment Service
**Language:** Node.js  
**Port:** 5000 (gRPC)  
**Responsibility:**
- Processes credit card charges
- Returns transaction IDs
- Mock implementation (doesn't charge real cards)

### 6. Shipping Service
**Language:** Go  
**Port:** 50051 (gRPC)  
**Responsibility:**
- Calculates shipping costs
- Provides shipping estimates
- Mock shipping functionality

### 7. Email Service
**Language:** Python  
**Port:** 8080 (gRPC)  
**Responsibility:**
- Sends order confirmation emails
- Mock SMTP (doesn't send real emails)

### 8. Currency Service
**Language:** Node.js  
**Port:** 7000 (gRPC)  
**Responsibility:**
- Converts prices between currencies
- Fetches real exchange rates from ECB
- High QPS service (most frequently called)

### 9. Recommendation Service
**Language:** Python  
**Port:** 8080 (gRPC)  
**Responsibility:**
- Provides product recommendations
- Suggests items based on cart contents
- Machine learning ready (currently rule-based)

### 10. Ad Service
**Language:** Java  
**Port:** 9555 (gRPC)  
**Responsibility:**
- Serves contextual ads
- Returns ads based on search keywords
- Ad targeting logic

### 11. Load Generator
**Language:** Python (Locust)  
**Port:** 8089 (HTTP)  
**Responsibility:**
- Simulates realistic user traffic
- Runs continuous load tests
- Performance testing

## 📡 Communication Patterns

### Inter-Service Communication: gRPC

**Why gRPC?**
- **Performance**: Binary protocol (faster than JSON)
- **Type Safety**: Protocol Buffers for contracts
- **Streaming**: Supports bidirectional streaming
- **Language Agnostic**: Works across different languages

**Example Service Call:**
```protobuf
// In protos/services.proto
service ProductCatalog {
  rpc ListProducts (Empty) returns (ListProductsResponse);
  rpc GetProduct (GetProductRequest) returns (Product);
}
```

```go
// In frontend service
client := pb.NewProductCatalogClient(conn)
products, err := client.ListProducts(context.Background(), &pb.Empty{})
```

### External Communication: HTTP/REST

**Frontend to User:**
```
User Browser
    ↓ (HTTP/HTTPS)
Frontend Service (8080)
    ↓ (Serves HTML/CSS/JS)
Browser renders UI
```

## 🗄️ Data Storage

### Redis Cache
**Used for:**
- Shopping cart storage
- Session data
- Cache layer for frequently accessed data

**Why Redis?**
- In-memory database
- Fast access
- TTL support for session expiration
- Pub/Sub capabilities

**Structure:**
```
Key: sessionId (e.g., "sess_12345")
Value: {
  "items": [
    {"productId": "1", "quantity": 2},
    {"productId": "5", "quantity": 1}
  ],
  "totalPrice": 150.00
}
```

## 🔄 Request Flow Example: Complete Purchase

```
1. User adds product to cart (Frontend → CartService)
   └─ CartService stores in Redis

2. User proceeds to checkout (Frontend → CheckoutService)
   
3. CheckoutService orchestrates:
   a. Get cart items (CheckoutService → CartService)
   b. Get product details (CheckoutService → ProductService)
   c. Convert prices (CheckoutService → CurrencyService)
   d. Process payment (CheckoutService → PaymentService)
   e. Calculate shipping (CheckoutService → ShippingService)
   f. Send email (CheckoutService → EmailService)
   
4. Return confirmation to user (Frontend displays order)

5. LoadGenerator continuously makes requests to simulate traffic
```

## 🌐 Network Topology

### Within Kubernetes Cluster

```yaml
# Service Discovery
Frontend can reach CartService via:
cartservice.default.svc.cluster.local:7070

# DNS Resolution
Kubernetes DNS automatically resolves service names
├─ servicename.namespace.svc.cluster.local
├─ Example: frontend.default.svc.cluster.local
└─ Used by gRPC clients for service lookup
```

### External Access

```yaml
# Option 1: LoadBalancer Service
External IP → Frontend Service

# Option 2: Ingress (Recommended)
External Domain → Ingress Controller → Frontend Service

# Option 3: NodePort
External IP:NodePort → Frontend Service
```

## 📊 Deployment Strategy

### Horizontal Pod Autoscaling (HPA)

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
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Result:**
- Monitors CPU usage
- When CPU > 70%: Scale up to max 10 replicas
- When CPU < 30%: Scale down to min 3 replicas
- Automatically handles traffic spikes

## 🔐 Security Architecture

### Network Security

```
┌─ Network Policies
│  ├─ Ingress rules (allow frontend access only)
│  └─ Egress rules (restrict outbound traffic)
│
├─ Pod Security Policies
│  ├─ Non-root users
│  ├─ Read-only filesystems
│  └─ No privilege escalation
│
├─ RBAC (Role-Based Access Control)
│  ├─ ServiceAccounts for each service
│  ├─ Minimal permissions per service
│  └─ No cluster-admin access
│
└─ Secrets Management
   ├─ Encrypted at rest
   ├─ TLS in transit
   └─ Separate secrets per environment
```

## 📈 Scalability Considerations

### Stateless Services
```
Frontend, ProductCatalog, CheckoutService → Easy to scale
Any replica can handle any request
No state synchronization needed
```

### Stateful Services
```
Redis (cart storage) → Requires clustering
Careful scaling to maintain data consistency
```

### Database Design
```
Current: JSON files (demo only)
Production: Real databases
├─ PostgreSQL for transactional data
├─ MongoDB for flexible schemas
└─ Redis for caching
```

## 🔍 Observability

### Three Pillars

1. **Metrics** (Prometheus)
   - Request count per service
   - Response latency
   - Error rates
   - CPU/Memory usage

2. **Logs** (ELK/Loki)
   - Application logs
   - Service interactions
   - Error details

3. **Traces** (Jaeger)
   - Request path through services
   - Latency per hop
   - Bottleneck identification

### Example Metrics Query
```promql
# P95 latency for Frontend service
histogram_quantile(0.95, 
  rate(grpc_server_handling_seconds_bucket{service="frontend"}[5m]))
```

## 🚀 Deployment Environments

### Development (Minikube)
```bash
├─ Single node cluster
├─ All services on one machine
├─ Docker Compose alternative
└─ For local testing
```

### Staging (Small GKE/EKS)
```bash
├─ 3-node cluster
├─ All services deployed
├─ Similar to production config
└─ For integration testing
```

### Production (Multi-region GKE/EKS)
```bash
├─ Multiple clusters
├─ Auto-scaling enabled
├─ Monitoring & alerts
├─ Backup & disaster recovery
└─ Blue-green deployments
```

---

## Summary

| Aspect | Pattern | Tool |
|--------|---------|------|
| Service Communication | gRPC | Protocol Buffers |
| External API | HTTP REST | Go/Node.js |
| State Storage | Redis | Redis |
| Orchestration | K8s Deployments | Kubernetes |
| Configuration | ConfigMaps | kubectl/Helm |
| Secrets | K8s Secrets | Sealed Secrets |
| Networking | Services/Ingress | Kubernetes |
| Autoscaling | HPA | Kubernetes |
| Monitoring | Prometheus | Grafana |

**Next:** See [01-DOCKER.md](01-DOCKER.md) to learn about containerization!
