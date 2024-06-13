pipeline {
    agent any

    environment {
        DOCKER_CREDENTIALS_ID = 'dockerhub-credentials'
        DOCKER_IMAGE = 'padster2012/test-chat'
        CHROME_DRIVER_VERSION = '114.0.5735.90'
        CHROME_INSTALL_DIR = "${WORKSPACE}/chrome"
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
        stage('Install Chrome and Dependencies') {
            steps {
                script {
                    echo 'Installing Chrome and necessary dependencies...'
                    sh '''#!/bin/bash
                    apt-get update
                    apt-get install -y \
                        wget \
                        gnupg2 \
                        unzip \
                        libxpm4 \
                        libxrender1 \
                        libgtk2.0-0 \
                        libnss3 \
                        libgconf-2-4 \
                        xvfb \
                        gtk2-engines-pixbuf \
                        xfonts-cyrillic \
                        xfonts-100dpi \
                        xfonts-75dpi \
                        xfonts-base \
                        xfonts-scalable \
                        imagemagick \
                        x11-apps \
                        x11-utils \
                        x11-xserver-utils

                    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
                    dpkg -x google-chrome-stable_current_amd64.deb google-chrome
                    mkdir -p ${CHROME_INSTALL_DIR}
                    mv google-chrome/opt/google/chrome/* ${CHROME_INSTALL_DIR}/
                    rm -rf google-chrome google-chrome-stable_current_amd64.deb

                    wget https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip
                    unzip -o chromedriver_linux64.zip -d ${CHROME_INSTALL_DIR}/
                    chmod +x ${CHROME_INSTALL_DIR}/chromedriver
                    rm chromedriver_linux64.zip
                    '''
                }
            }
        }
        stage('Start Application') {
            steps {
                script {
                    echo 'Starting the Python application...'
                    sh '''#!/bin/bash
                    source ./venv/bin/activate
                    nohup python app.py &
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
                    sh '''#!/bin/bash
                    export DISPLAY=:99.0
                    export PATH=${CHROME_INSTALL_DIR}:$PATH
                    nohup Xvfb :99 -ac &
                    sleep 3
                    echo "Installed Chrome version:"
                    ${CHROME_INSTALL_DIR}/chrome --version
                    echo "Running tests..."
                    ./venv/bin/python -m unittest discover -s tests -p "*.py"
                    '''
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
