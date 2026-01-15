pipeline {
    agent any

    environment {
        DOCKER_HOST = "tcp://host.docker.internal:2375"
        IMAGE_API = "narjess010/bot-api:latest"
        IMAGE_FRONTEND = "narjess010/bot-frontend:latest"
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
                    bat "docker build -t %IMAGE_API% -f src/api/Dockerfile ."
                    bat "docker build -t %IMAGE_FRONTEND% -f src/frontend/Dockerfile ."
                    bat "docker images"
                }
            }
        }

        stage('Push Docker Images') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                        echo "Logging into DockerHub..."
                        bat 'echo %PASS% | docker login -u %USER% --password-stdin'
                    }
                    echo "Pushing API image..."
                    bat "docker push %IMAGE_API%"
                    echo "Pushing Frontend image..."
                    bat "docker push %IMAGE_FRONTEND%"
                }
            }
        }

        stage('Deploy with Docker Compose') {
            steps {
                script {
                    echo "Stopping any running containers..."
                    bat "docker compose -f %COMPOSE_FILE% down || exit 0"

                    echo "Starting containers..."
                    bat "docker compose -f %COMPOSE_FILE% up -d --build"

                    echo "List of running containers:"
                    bat "docker ps -a"
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
            bat "docker ps -a"
        }
    }
}

