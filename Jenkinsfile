pipeline {
    agent any

    environment {
        IMAGE_API = "bot-api:latest"
        IMAGE_FRONTEND = "bot-frontend:latest"
        COMPOSE_FILE = "src/docker-compose.yml"
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
                    // Construire API
                    sh 'docker build -t $IMAGE_API -f src/api/Dockerfile .'

                    // Construire Frontend
                    sh 'docker build -t $IMAGE_FRONTEND -f src/frontend/Dockerfile .'
                }
            }
        }

        stage('Run Docker Compose') {
            steps {
                script {
                    sh 'docker compose -f $COMPOSE_FILE down || true'
                    sh 'docker compose -f $COMPOSE_FILE up -d --build'
                }
            }
        }

        stage('Clean Up') {
            steps {
                script {
                    sh 'docker compose -f $COMPOSE_FILE down'
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline terminée"
        }
    }
}

