pipeline {
    agent any

    environment {
        DOCKER_CREDENTIALS_ID = 'dockerhub-credentials'
        DOCKER_IMAGE = 'padster2012/test-chat'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out the source code...'
                git branch: 'main', url: 'https://github.com/PadsterH2012/chatroom-project.git'
            }
        }
        stage('Setup Python Environment') {
            steps {
                script {
                    echo 'Setting up Python environment...'
                    sh 'python3 -m venv venv'
                    sh './venv/bin/pip install -r requirements.txt'
                }
            }
        }
        stage('Run Unit Tests') {
            steps {
                script {
                    echo 'Running unit tests...'
                    // List the directory structure for debugging
                    sh 'ls -R'
                    // Run unit tests
                    sh './venv/bin/python -m unittest discover -s tests -p "*.py"'
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                script {
                    echo 'Building Docker image...'
                    // Ensure the correct shell is used
                    sh '''#!/bin/bash
                    docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} .
                    '''
                }
            }
        }
        stage('Push Docker Image') {
            steps {
                script {
                    echo 'Pushing Docker image to DockerHub...'
                    // Ensure the correct shell is used
                    withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDENTIALS_ID}", usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                        sh '''#!/bin/bash
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}
                        '''
                    }
                }
            }
        }
    }
}
