# Documentation Index

Welcome to the Microservices Demo learning repository! This guide will help you become a DevOps engineer.

## 📚 Documentation Structure

### Getting Started
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Setup your environment and run the application
  - Prerequisites
  - Installation steps
  - Quick start (5 minutes)
  - Common tasks

### Learning Materials
- **[00-LEARNING_ROADMAP.md](00-LEARNING_ROADMAP.md)** - Structured learning path
  - Phase 1: Fundamentals
  - Phase 2: Containerization
  - Phase 3: Kubernetes & Orchestration
  - Phase 4: Advanced Topics
  - Phase 5: Production Ready

- **[DEVOPS_CONCEPTS.md](DEVOPS_CONCEPTS.md)** - Core DevOps concepts explained
  - Containerization
  - Orchestration
  - Infrastructure as Code
  - CI/CD
  - Monitoring
  - Security
  - Scalability
  - High Availability
  - GitOps

### Technical Deep Dives
- **[01-ARCHITECTURE.md](01-ARCHITECTURE.md)** - Microservices architecture breakdown
  - System overview
  - Service descriptions
  - Communication patterns
  - Data storage
  - Request flow example
  - Network topology
  - Deployment strategy
  - Security architecture
  - Observability

- **[02-DOCKER.md](02-DOCKER.md)** - Docker and containerization
  - Docker fundamentals
  - Writing Dockerfiles
  - Best practices
  - Multi-stage builds
  - Building & pushing images
  - Docker Compose

- **[03-KUBERNETES.md](03-KUBERNETES.md)** - Kubernetes orchestration
  - Kubernetes fundamentals
  - Core resources (Pod, Deployment, Service, ConfigMap, Secret)
  - Deployment manifests
  - Services & networking
  - Configuration management
  - StatefulSets
  - Advanced patterns (HPA, PDB)
  - Hands-on exercises

- **[04-CICD.md](04-CICD.md)** - CI/CD pipelines
  - GitHub Actions basics
  - Build & push pipeline
  - Test pipeline
  - Deployment pipeline
  - Complete workflows
  - Setting up secrets

## 🎯 Learning Paths by Role

### For Developers Learning DevOps
```
1. Read: DEVOPS_CONCEPTS.md
2. Read: 01-ARCHITECTURE.md (understand the system)
3. Follow: GETTING_STARTED.md (set up environment)
4. Complete: 02-DOCKER.md exercises (containerization)
5. Complete: 03-KUBERNETES.md exercises (local K8s)
6. Deploy: Use 04-CICD.md to set up automated deployments
```

### For Operations/Infrastructure Engineers
```
1. Read: 01-ARCHITECTURE.md (understand requirements)
2. Complete: 03-KUBERNETES.md (cluster management)
3. Read: 04-CICD.md (deployment pipelines)
4. Study: Terraform configs for infrastructure
5. Set up: Monitoring and logging
6. Document: Runbooks and troubleshooting guides
```

### For DevOps Engineers
```
1. Complete all learning materials
2. Set up GKE/EKS cluster (real cloud)
3. Implement monitoring stack
4. Automate disaster recovery
5. Implement GitOps workflow
6. Security hardening
7. Performance optimization
```

## 🚀 Quick Navigation

### I want to...

**Run the application locally**
→ [GETTING_STARTED.md](GETTING_STARTED.md) → Option 1: Docker Compose

**Deploy to Kubernetes locally**
→ [GETTING_STARTED.md](GETTING_STARTED.md) → Option 2: Minikube

**Understand how everything works**
→ Start with [DEVOPS_CONCEPTS.md](DEVOPS_CONCEPTS.md) → [01-ARCHITECTURE.md](01-ARCHITECTURE.md)

**Learn Docker**
→ [02-DOCKER.md](02-DOCKER.md)

**Learn Kubernetes**
→ [03-KUBERNETES.md](03-KUBERNETES.md)

**Set up CI/CD**
→ [04-CICD.md](04-CICD.md)

**Troubleshoot issues**
→ [GETTING_STARTED.md#troubleshooting](GETTING_STARTED.md#troubleshooting)

## 📊 Project Structure Reference

```
microservices-demo/
├── docs/                          # All documentation
│   ├── GETTING_STARTED.md        # Start here!
│   ├── DEVOPS_CONCEPTS.md        # Theory
│   ├── 00-LEARNING_ROADMAP.md    # Learning path
│   ├── 01-ARCHITECTURE.md        # System design
│   ├── 02-DOCKER.md              # Containerization
│   ├── 03-KUBERNETES.md          # Orchestration
│   └── 04-CICD.md                # Automation
│
├── src/                           # Application source code
│   ├── frontend/                 # Go HTTP server
│   ├── cartservice/              # C# service
│   ├── productcatalogservice/    # Go service
│   ├── currencyservice/          # Node.js service
│   ├── paymentservice/           # Node.js service
│   ├── shippingservice/          # Go service
│   ├── emailservice/             # Python service
│   ├── checkoutservice/          # Go service
│   ├── recommendationservice/    # Python service
│   ├── adservice/                # Java service
│   └── loadgenerator/            # Python/Locust
│
├── kubernetes/                    # Kubernetes manifests
│   ├── base/                     # Base configurations
│   │   ├── frontend.yaml         # Frontend deployment
│   │   └── kustomization.yaml
│   └── overlays/                 # Environment-specific
│       ├── dev/
│       ├── staging/
│       └── production/
│
├── helm/                          # Helm charts (coming)
├── terraform/                     # Infrastructure as Code (coming)
├── .github/workflows/             # CI/CD pipelines
├── scripts/                       # Utility scripts
├── docker-compose.yml             # Local development
└── README.md                      # Main readme
```

## 🎓 Key Concepts Checklist

After completing this learning, you should understand:

### Docker
- [ ] What is a container vs VM
- [ ] How to write a Dockerfile
- [ ] Multi-stage builds
- [ ] Image layers and caching
- [ ] Docker Compose
- [ ] Running containers locally

### Kubernetes
- [ ] Pod, Deployment, Service basics
- [ ] ConfigMap and Secret management
- [ ] Probes (liveness, readiness, startup)
- [ ] Horizontal Pod Autoscaling
- [ ] Ingress and networking
- [ ] Namespace isolation
- [ ] StatefulSets for databases

### DevOps Practices
- [ ] Infrastructure as Code
- [ ] CI/CD pipeline architecture
- [ ] Monitoring and observability
- [ ] Security best practices
- [ ] High availability and disaster recovery
- [ ] GitOps workflows

## 💡 Pro Tips

1. **Read with code reference**
   - Keep the actual manifests open while reading
   - Look at `kubernetes/base/frontend.yaml` when reading about Deployments

2. **Hands-on practice**
   - Don't just read, follow the exercises
   - Break things and fix them (you'll learn faster)

3. **Experiment**
   - Try scaling pods: `kubectl scale deployment frontend --replicas=10`
   - Try updating images: `kubectl set image deployment/frontend frontend=new:image`
   - Try deleting pods: `kubectl delete pod <pod-name>` (watch Kubernetes recreate it)

4. **Reference the code**
   - Check actual service Dockerfiles in `src/*/Dockerfile`
   - Study real manifests in `kubernetes/base/`
   - Examine CI/CD workflow in `.github/workflows/`

5. **Join communities**
   - Kubernetes Slack
   - DevOps Reddit communities
   - CNCF events
   - Local tech meetups

## 📖 External Resources

### Official Documentation
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [Docker Docs](https://docs.docker.com/)
- [Helm Docs](https://helm.sh/docs/)
- [gRPC Docs](https://grpc.io/docs/)
- [Terraform Docs](https://www.terraform.io/docs/)

### YouTube Channels
- [Nana Janashvili](https://www.techworld-with-nana.com/)
- [KodeKloud](https://www.kodekloud.com/)
- [DevOps Toolkit](https://www.youtube.com/c/DevOpsToolkit)
- [That DevOps Guy](https://www.youtube.com/c/thatdevopsguy)

### Books
- "The Phoenix Project" - DevOps principles
- "Site Reliability Engineering" - Google's approach
- "The DevOps Handbook" - Practical guide

### Interactive Learning
- [KubernetesByExample.com](https://www.kubernetesbyexample.com/)
- [DockerLabs](https://dockerlabs.collabnix.com/)
- [Play with Kubernetes](https://labs.play-with-k8s.com/)

## 🆘 Getting Help

1. **Check the troubleshooting section** in [GETTING_STARTED.md](GETTING_STARTED.md)

2. **Debug commands:**
   ```bash
   # View pod details
   kubectl describe pod <pod-name> -n online-boutique
   
   # View logs
   kubectl logs <pod-name> -n online-boutique
   
   # Get events
   kubectl get events -n online-boutique --sort-by='.lastTimestamp'
   
   # Access pod shell
   kubectl exec -it <pod-name> -n online-boutique -- /bin/sh
   ```

3. **Check Kubernetes events:**
   ```bash
   kubectl get events -n online-boutique
   ```

4. **Check if services are running:**
   ```bash
   kubectl get all -n online-boutique
   ```

## 📝 Notes for Contributors

This repository is designed for learning. If you want to:

- **Add documentation** - Follow the existing format
- **Add exercises** - Include step-by-step instructions
- **Fix errors** - Submit a PR with explanations
- **Add new services** - Document the service and update architecture

## 🎉 Success Criteria

You'll know you've mastered this material when you can:

1. ✅ Deploy an application to local Kubernetes without looking at notes
2. ✅ Explain the architecture to someone else
3. ✅ Write a Dockerfile with multi-stage builds
4. ✅ Create a Kubernetes Deployment with probes and resource limits
5. ✅ Set up a CI/CD pipeline with GitHub Actions
6. ✅ Scale an application and monitor it
7. ✅ Debug a failing pod
8. ✅ Deploy infrastructure with Terraform
9. ✅ Recover from a service failure
10. ✅ Build a complete microservices system on a real cloud provider

---

## 🚀 Ready to Start?

**Beginners:** Start with [GETTING_STARTED.md](GETTING_STARTED.md)

**Experienced Engineers:** Jump to [04-CICD.md](04-CICD.md)

**Want the full picture first?** Read [DEVOPS_CONCEPTS.md](DEVOPS_CONCEPTS.md)

---

Happy Learning! 📚🚀

*Last Updated: April 2026*
*Part of the DevOps & Kubernetes Learning Journey with Nana*
