
# DevOps Lab CI/CD Project (Jenkins + Docker + Kubernetes + Prometheus/Grafana)

This repository contains a minimal Flask web application backed by PostgreSQL and a complete CI/CD pipeline using Jenkins. The pipeline builds a Docker image, pushes it to Docker Hub, deploys to Kubernetes, and sets up monitoring with Prometheus and Grafana.

## Prerequisites
- AWS EC2 (Ubuntu 22.04 LTS recommended) with security group ports open for 22, 80/30000+ (if using NodePort), 8080 (Jenkins), and optional 3000 (Grafana), 9090 (Prometheus)
- Docker & kubectl installed on the Jenkins node
- Access to a Kubernetes cluster (e.g., EKS, k3s, kind, Minikube)
- Jenkins with plugins: Git, Pipeline, Docker Pipeline, Kubernetes CLI, Prometheus
- Docker Hub account + Jenkins credentials (ID: `dockerhub-creds`)

## Repo Structure
```
.
├── Jenkinsfile
├── Dockerfile
├── app/
│   ├── app.py
│   └── requirements.txt
└── k8s/
    ├── namespace.yaml
    ├── secret.yaml
    ├── configmap.yaml
    ├── postgres-pvc.yaml
    ├── postgres-deployment.yaml
    ├── postgres-service.yaml
    ├── app-deployment.yaml
    ├── app-service.yaml
    └── monitoring/
        └── service-monitor.yaml
```

## How to Use
1. **Clone & Replace placeholders**
   - In `k8s/app-deployment.yaml` and `Jenkinsfile`, replace `DOCKERHUB_USERNAME` with your Docker Hub username.
   - In `Jenkinsfile`, set your GitHub repo URL in the `Fetch Code` stage.
2. **Configure Jenkins Credentials**
   - Add *Username with password* credentials for Docker Hub using ID `dockerhub-creds`.
   - (Optional) Add a *Secret file* for kubeconfig with ID `kubeconfig-file` and ensure `kubectl` uses it.
3. **Create GitHub Webhook** pointing to Jenkins `http://<jenkins-host>:8080/github-webhook/`.
4. **Run the Pipeline**. On success, the app will be in namespace `devops-lab` and monitored by Prometheus/Grafana.

## Accessing the App
- Inside cluster: `kubectl -n devops-lab port-forward svc/demo-app 8081:80` then open http://localhost:8081
- Endpoints:
  - `GET /` health page
  - `GET /items` list items
  - `POST /items` with JSON `{"name": "foo"}` to insert
  - `GET /metrics` Prometheus metrics

## Monitoring
- Install occurs via Helm (`kube-prometheus-stack`). Grafana admin password is set to `admin123` (change in Jenkinsfile).
- Access Grafana: `kubectl -n monitoring port-forward svc/monitoring-grafana 3000:80` then open http://localhost:3000
- Add dashboard: Kubernetes / Pod monitoring and custom Prometheus queries.

## Clean Up
```
kubectl delete ns devops-lab monitoring
```

## Notes
- PVC uses default StorageClass; ensure your cluster has a default provisioner.
- For production use, prefer PostgreSQL StatefulSet.
