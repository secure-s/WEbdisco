
pipeline {
  agent any

  environment {
    DOCKERHUB_CREDENTIALS = 'dockerhub-creds' // Jenkins credentialsId (Username with password)
    DOCKERHUB_USERNAME = 'DOCKERHUB_USERNAME' // TODO: replace with your Docker Hub username
    APP_IMAGE = "${DOCKERHUB_USERNAME}/devops-lab-app:${env.BUILD_NUMBER}"
    APP_IMAGE_LATEST = "${DOCKERHUB_USERNAME}/devops-lab-app:latest"
    KUBE_NAMESPACE = 'devops-lab'
    KUBECONFIG = credentials('kubeconfig-file') // Jenkins File credential (Secret file) optional
  }

  options {
    timestamps()
    ansiColor('xterm')
  }

  stages {
    stage('Fetch Code') {
      steps {
        checkout([$class: 'GitSCM', branches: [[name: '*/main']], userRemoteConfigs: [[url: 'https://github.com/your-username/your-repo.git']]])
      }
    }

    stage('Build & Push Docker Image') {
      steps {
        sh 'echo "Building image ${APP_IMAGE}"'
        withCredentials([usernamePassword(credentialsId: env.DOCKERHUB_CREDENTIALS, passwordVariable: 'DOCKERHUB_PASSWORD', usernameVariable: 'DOCKERHUB_USER')]) {
          sh '''
            echo "$DOCKERHUB_PASSWORD" | docker login -u "$DOCKERHUB_USER" --password-stdin
            docker build -t ${APP_IMAGE} -t ${APP_IMAGE_LATEST} .
            docker push ${APP_IMAGE}
            docker push ${APP_IMAGE_LATEST}
          '''
        }
      }
    }

    stage('Kubernetes Deploy') {
      steps {
        sh '''
          kubectl create namespace ${KUBE_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
          # Replace image in deployment manifest
          sed -i "s|DOCKERHUB_USERNAME/devops-lab-app:latest|${APP_IMAGE_LATEST}|g" k8s/app-deployment.yaml

          kubectl apply -f k8s/namespace.yaml
          kubectl apply -f k8s/secret.yaml
          kubectl apply -f k8s/configmap.yaml
          kubectl apply -f k8s/postgres-pvc.yaml
          kubectl apply -f k8s/postgres-deployment.yaml
          kubectl apply -f k8s/postgres-service.yaml
          kubectl apply -f k8s/app-deployment.yaml
          kubectl apply -f k8s/app-service.yaml

          kubectl rollout status deploy/postgres -n ${KUBE_NAMESPACE} --timeout=120s || true
          kubectl rollout status deploy/demo-app -n ${KUBE_NAMESPACE} --timeout=180s || true
        '''
      }
    }

    stage('Monitoring: Prometheus & Grafana') {
      steps {
        sh '''
          # Install Helm if missing
          if ! command -v helm >/dev/null 2>&1; then
            curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
          fi

          kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

          helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
          helm repo update
          # Install/upgrade kube-prometheus-stack
          helm upgrade --install monitoring prometheus-community/kube-prometheus-stack             --namespace monitoring             --set grafana.adminPassword='admin123'             --wait --timeout 10m

          # Create ServiceMonitor for app (requires kube-prometheus-stack CRDs)
          kubectl apply -f k8s/monitoring/service-monitor.yaml
        '''
      }
    }
  }

  post {
    always {
      sh 'kubectl get pods -A'
      archiveArtifacts artifacts: '**/*.yaml', fingerprint: true
    }
  }
}
