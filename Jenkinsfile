pipeline {
    agent any

    environment {
        DOCKER_HOST = "tcp://host.docker.internal:2375"
        IMAGE_API = "bot-api:latest"
        IMAGE_FRONTEND = "bot-frontend:latest"
        COMPOSE_FILE = "docker-compose.yml"
    }

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/NAILINARJESS/mlops_docker_repo.git', branch: 'main'
            }
        }

        stage('Build Docker Images') {
            steps {
                script {
                    echo "Building Docker images..."
                    sh 'docker build -t $IMAGE_API -f src/api/Dockerfile .'
                    sh 'docker build -t $IMAGE_FRONTEND -f src/frontend/Dockerfile .'
                    sh 'docker images' // Vérifie que les images ont été créées
                }
            }
        }

        stage('Deploy with Docker Compose') {
            steps {
                script {
                    echo "Stopping any running containers..."
                    sh 'docker compose -f $COMPOSE_FILE down || true'

                    echo "Starting containers..."
                    sh 'docker compose -f $COMPOSE_FILE up -d --build'

                    echo "List of running containers:"
                    sh 'docker ps -a'
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline terminée avec succès. Les containers tournent toujours."
        }
        failure {
            echo "La pipeline a échoué. Vérifiez les logs et les containers."
            sh 'docker ps -a'
        }
    }
}

