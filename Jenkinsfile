pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: docker
    image: docker:20.10.16-dind
    command:
    - cat
    tty: true
    securityContext:
      privileged: true
    volumeMounts:
    - name: docker-sock
      mountPath: /var/run/docker.sock
  - name: python
    image: python:3.10-slim
    command:
    - cat
    tty: true
  volumes:
  - name: docker-sock
    hostPath:
      path: /var/run/docker.sock
"""
        }
    }
    
    environment {
        DOCKER_REGISTRY = 'registry.example.com'
        IMAGE_NAME = 'infra-automation'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        DOCKER_COMPOSE_VERSION = '2.15.1'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install Dependencies') {
            steps {
                container('python') {
                    sh 'pip install -r requirements.txt'
                    sh 'pip install pytest pytest-asyncio pytest-cov'
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                container('python') {
                    sh 'TESTING=1 python -m pytest src/tests/ -v --cov=src --cov-report=xml:coverage.xml --junitxml=test-results.xml'
                }
            }
            post {
                always {
                    junit 'test-results.xml'
                    cobertura coberturaReportFile: 'coverage.xml'
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                container('docker') {
                    sh 'docker build -t ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} .'
                    sh 'docker tag ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest'
                }
            }
        }
        
        stage('Push Docker Image') {
            when {
                branch 'main'
            }
            steps {
                container('docker') {
                    withCredentials([usernamePassword(credentialsId: 'docker-registry-credentials', usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                        sh 'echo $DOCKER_PASSWORD | docker login ${DOCKER_REGISTRY} -u ${DOCKER_USERNAME} --password-stdin'
                        sh 'docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}'
                        sh 'docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest'
                    }
                }
            }
        }
        
        stage('Deploy to Development') {
            when {
                branch 'main'
            }
            steps {
                container('docker') {
                    withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                        sh 'curl -LO "https://dl.k8s.io/release/stable.txt"'
                        sh 'curl -LO "https://dl.k8s.io/release/$(cat stable.txt)/bin/linux/amd64/kubectl"'
                        sh 'chmod +x kubectl'
                        sh './kubectl --kubeconfig=$KUBECONFIG set image deployment/infra-automation infra-automation=${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} -n development'
                    }
                }
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            input {
                message "Deploy to production?"
                ok "Yes"
            }
            steps {
                container('docker') {
                    withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                        sh './kubectl --kubeconfig=$KUBECONFIG set image deployment/infra-automation infra-automation=${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} -n production'
                    }
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
} 