pipeline {
    agent any

    environment {
        PYTHON = "python"                        // ou chemin complet si nécessaire
        DOCKERHUB_CREDENTIALS = "dockerhub-credentials"
        GITHUB_CREDENTIALS = "github-credentials"
        DAGSHUB_TOKEN = credentials("dagshub-token")
    }

    stages {

        // 1️⃣ Checkout
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/NAILINARJESS/mlops_docker_repo.git',
                    credentialsId: "${GITHUB_CREDENTIALS}"
            }
        }

        // 2️⃣ Setup / Environment
        stage('Setup Environment') {
            steps {
                bat """
                python -m venv venv
                venv\\Scripts\\pip install --upgrade pip
                venv\\Scripts\\pip install -r requirements.txt
                """
            }
        }

        // 3️⃣ Data Collection (optionnel)
        stage('Data Collection') {
            steps {
                bat "venv\\Scripts\\python src/data/collect_data.py || echo 'No new data'"
            }
        }

        // 4️⃣ ML Pipeline: Preprocessing + Training + MLflow
        stage('ML Training & Tracking') {
            steps {
                bat """
                set DAGSHUB_TOKEN=${DAGSHUB_TOKEN}
                venv\\Scripts\\python src/tracking/mlflow_tracking.py
                """
            }
        }

        // 5️⃣ Build Docker Images
        stage('Build Docker Images') {
            steps {
                bat """
                docker build -t bot-api -f src/api/Dockerfile .
                docker build -t bot-frontend -f src/frontend/Dockerfile src/frontend
                """
            }
        }

        // 6️⃣ Docker Compose
        stage('Docker Compose Up') {
            steps {
                bat "docker-compose -f src/docker-compose.yml up -d --build"
            }
        }

        // 7️⃣ Run Tests
        stage('Run Tests') {
            steps {
                bat "venv\\Scripts\\pytest src/tests --maxfail=1 --disable-warnings -v"
            }
        }

        // 8️⃣ Push Docker Hub (optionnel)
        stage('Push Docker Images') {
            steps {
                withCredentials([usernamePassword(credentialsId: "${DOCKERHUB_CREDENTIALS}", usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    bat """
                    docker login -u %DOCKER_USER% -p %DOCKER_PASS%
                    docker tag bot-api %DOCKER_USER%/bot-api:latest
                    docker tag bot-frontend %DOCKER_USER%/bot-frontend:latest
                    docker push %DOCKER_USER%/bot-api:latest
                    docker push %DOCKER_USER%/bot-frontend:latest
                    """
                }
            }
        }

        // 9️⃣ Cleanup
        stage('Cleanup') {
            steps {
                bat "docker-compose -f src/docker-compose.yml down"
            }
        }
    }

    post {
        always {
            echo "Pipeline terminé."
        }
        success {
            echo "✅ Build & Déploiement réussis."
        }
        failure {
            echo "❌ Une erreur est survenue."
        }
    }
}

