pipeline { 
    agent any

    environment {
        DOCKER_HOST = "tcp://host.docker.internal:2375"
        IMAGE_API = "bot-api:latest"
        IMAGE_FRONTEND = "bot-frontend:latest"
        COMPOSE_FILE = "docker-compose.yml"
        DOCKERHUB_CREDENTIALS = "dockerhub-credentials"
        GITHUB_CREDENTIALS = "github-credentials"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Checkout du repository..."
                git url: 'https://github.com/NAILINARJESS/mlops_docker_repo.git', 
                    branch: 'main', 
                    credentialsId: "${GITHUB_CREDENTIALS}"
            }
        }

        stage('Build Docker Images') {
            steps {
                echo "Building Docker API image..."
                sh "docker build -t $IMAGE_API -f src/api/Dockerfile ."
                
                echo "Building Docker Frontend image..."
                // Build context limité au dossier src/frontend
                sh "docker build -t $IMAGE_FRONTEND -f src/frontend/Dockerfile src/frontend"
                
                sh "docker images"
            }
        }

        stage('Push Docker Images to Docker Hub') {
            steps {
                echo "Pushing Docker images to Docker Hub..."
                withCredentials([usernamePassword(
                    credentialsId: "${DOCKERHUB_CREDENTIALS}", 
                    usernameVariable: 'DOCKER_USER', 
                    passwordVariable: 'DOCKER_PASS')]) {
                    
                    sh """
                        echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin
                        docker tag $IMAGE_API \$DOCKER_USER/bot-api:latest
                        docker tag $IMAGE_FRONTEND \$DOCKER_USER/bot-frontend:latest
                        docker push \$DOCKER_USER/bot-api:latest
                        docker push \$DOCKER_USER/bot-frontend:latest
                    """
                }
            }
        }

        stage('Deploy with Docker Compose') {
            steps {
                echo "Stopping any running containers..."
                sh "docker compose -f $COMPOSE_FILE down || true"
                
                echo "Starting containers..."
                sh "docker compose -f $COMPOSE_FILE up -d --build"
                
                sh "docker ps -a"
            }
        }
    }

    post {
        always {
            echo "Pipeline terminée. Les containers tournent et les images sont sur Docker Hub."
        }
        success {
            echo "✅ Pipeline CI/CD réussi !"
        }
        failure {
            echo "❌ Pipeline échoué. Vérifie les logs pour corriger les erreurs."
        }
    }
}

