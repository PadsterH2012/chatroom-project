pipeline {
    agent any

    environment {
        DOCKER_CREDENTIALS_ID = 'dockerhub-credentials'
        DOCKER_IMAGE = 'padster2012/test-chat'
        CHROME_DRIVER_VERSION = '114.0.5735.90'
        CHROME_INSTALL_DIR = "${WORKSPACE}/chrome"
        CHROME_BINARY = '/usr/bin/google-chrome'
    }

    stages {
        stage('Clean Workspace') {
            steps {
                deleteDir()  // Clean the workspace before starting the build
            }
        }
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
                    sh './venv/bin/pip install Flask selenium webdriver-manager'
                }
            }
        }
        stage('Install Chrome and Dependencies') {
            steps {
                script {
                    echo 'Installing Chrome and necessary dependencies...'
                    withCredentials([string(credentialsId: 'jenkins-sudo-password', variable: 'SUDO_PASSWORD')]) {
                        sh '''#!/bin/bash
                        echo $SUDO_PASSWORD | sudo -S apt-get update
                        echo $SUDO_PASSWORD | sudo -S apt-get install -y \
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
                            x11-xserver-utils \
                            python3-pip \
                            python3-venv

                        wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
                        echo $SUDO_PASSWORD | sudo -S dpkg -i google-chrome-stable_current_amd64.deb || echo $SUDO_PASSWORD | sudo -S apt-get -f install -y

                        wget https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip
                        unzip -o chromedriver_linux64.zip -d ${CHROME_INSTALL_DIR}/
                        chmod +x ${CHROME_INSTALL_DIR}/chromedriver
                        rm chromedriver_linux64.zip
                        rm google-chrome-stable_current_amd64.deb
                        '''
                    }
                }
            }
        }
        stage('Setup Python Environment') {
            steps {
                script {
                    echo 'Setting up Python virtual environment...'
                    sh '''#!/bin/bash
                    python3 -m venv venv
                    source venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    '''
                }
            }
        }
        stage('Start Application') {
            steps {
                script {
                    echo 'Starting the Python application...'
                    sh '''
                    source venv/bin/activate
                    export DISPLAY=:0.0  # Ensure correct display is set
                    nohup python app.py &
                    sleep 10  # Give the application time to start
                    '''
                }
            }
        }
        stage('Run Tests') {
            steps {
                script {
                    echo 'Running unit and UI tests...'
                    sh '''#!/bin/bash
                    source venv/bin/activate
                    export DISPLAY=:0.0  # Use the real display
                    echo "Installed Chrome version:"
                    google-chrome --version
                    echo "Running tests..."
                    set +e  # Allow the script to continue even if tests fail
                    ./venv/bin/python -m unittest discover -s tests -p "*.py" > test_results.log
                    TEST_RESULT=$?
                    set -e  # Re-enable exit on error
                    cat test_results.log
                    exit $TEST_RESULT
                    '''
                }
            }
        }
        // stage('Cleanup') {
        //     steps {
        //         script {
        //             echo 'Cleaning up...'
        //             sh '''#!/bin/bash
        //             pkill -f "python app.py"
        //             rm -rf venv
        //             '''
        //         }
        //     }
        // }
        // stage('Build Docker Image') {
        //     steps {
        //         script {
        //             echo 'Building Docker image...'
        //             sh '''#!/bin/bash
        //             docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} .
        //             '''
        //         }
        //     }
        // }
        // stage('Push Docker Image') {
        //     steps {
        //         script {
        //             echo 'Pushing Docker image to DockerHub...'
        //             withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDENTIALS_ID}", usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
        //                 sh '''#!/bin/bash
        //                 echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
        //                 docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}
        //                 '''
        //             }
        //         }
        //     }
        // }
    }
}
