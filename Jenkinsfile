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
                    sh './venv/bin/pip install selenium webdriver-manager'
                }
            }
        }
        stage('Start Application') {
            steps {
                script {
                    echo 'Starting the Python application...'
                    sh '''#!/bin/bash
                    source ./venv/bin/activate
                    python app.py &
                    '''
                    // Give the app some time to start
                    sleep 10
                }
            }
        }
        stage('Run Tests') {
            steps {
                script {
                    echo 'Running unit and UI tests...'
                    sh './venv/bin/python -m unittest discover -s tests -p "*.py"'
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                script {
                    echo 'Building Docker image...'
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
                    withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDENTIALS_ID}", usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                        sh '''#!/bin/bash
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}
                        '''
                    }
                }
            }
        }
        stage('Stop Application') {
            steps {
                script {
                    echo 'Stopping application...'
                    sh '''#!/bin/bash
                    pkill -f "python app.py"
                    '''
                }
            }
        }
    }
}
