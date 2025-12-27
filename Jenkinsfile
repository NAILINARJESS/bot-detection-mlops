pipeline {
    agent { label 'windows' }  // mettre le label exact de ton node Windows

    environment {
        PYTHON = "python"
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

        // 3️⃣ ML Pipeline: Preprocessing + Training + MLflow
        stage('ML Training & Tracking') {
            steps {
                bat """
                set DAGSHUB_TOKEN=${DAGSHUB_TOKEN}
                venv\\Scripts\\python src\\tracking\\mlflow_tracking.py
                """
            }
        }

        // 4️⃣ Build Docker Images
        stage('Build Docker Images') {
            steps {
                bat """
                docker build -t bot-api -f src\\api\\Dockerfile .
                docker build -t bot-frontend -f src\\frontend\\Dockerfile src\\frontend
                """
            }
        }

        // 5️⃣ Docker Compose Up
        stage('Docker Compose Up') {
            steps {
                bat "docker-compose -f src\\docker-compose.yml up -d --build"
            }
        }

        // 6️⃣ Cleanup
        stage('Cleanup') {
            steps {
                bat "docker-compose -f src\\docker-compose.yml down"
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

