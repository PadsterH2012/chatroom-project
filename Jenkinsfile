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
        stage('Install Chrome and ChromeDriver') {
            steps {
                script {
                    echo 'Installing Chrome and ChromeDriver...'
                    sh '''#!/bin/bash
                    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
                    sudo apt install -y ./google-chrome-stable_current_amd64.deb
                    wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip
                    unzip chromedriver_linux64.zip
                    sudo mv chromedriver /usr/local/bin/
                    sudo chmod +x /usr/local/bin/chromedriver
                    '''
                }
            }
        }
        stage('Run Unit Tests') {
            steps {
                script {
                    echo 'Running unit tests...'
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
        stage('Start Application') {
            steps {
                script {
                    echo 'Starting application...'
                    sh '''#!/bin/bash
                    docker run -d --name my_app -p 5000:5000 ${DOCKER_IMAGE}:${BUILD_NUMBER}
                    '''
                }
            }
        }
        stage('Run UI Tests') {
            steps {
                script {
                    echo 'Running UI tests...'
                    sh './venv/bin/python -m unittest discover -s tests -p "test_ui.py"'
                }
            }
        }
        stage('Stop Application') {
            steps {
                script {
                    echo 'Stopping application...'
                    sh '''#!/bin/bash
                    docker stop my_app
                    docker rm my_app
                    '''
                }
            }
        }
    }
}
