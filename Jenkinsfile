pipeline {
  agent any

  environment {
    DJANGO_SETTINGS_MODULE = 'backend.jenkins_settings'

  }

  stages {
    stage('Installation') {
      steps {
        sh './dev-tools/install.sh'
      }
    }
    stage('Testing') {
      parallel {
        stage('Linting') {
          steps {
            sh '. .venv/bin/activate && cd backend && pylint_runner'
          }
        }
        stage('Test Cases') {
          steps {
            withCredentials([usernamePassword(credentialsId: 'cms_django_database', passwordVariable: 'CMS_DJANGO_DATABASE_PASSWORD', usernameVariable: 'CMS_DJANGO_DATABASE_USER')]) {
                sh '. .venv/bin/activate && integreat-cms makemigrations cms && integreat-cms migrate'
                sh '. .venv/bin/activate && integreat-cms test cms'
            }
          }
        }
      }
    }
    stage('Packaging') {
      steps {
        sh './dev-tools/install.sh'
        sh '. .venv/bin/activate && pip3 install stdeb'
        sh '. .venv/bin/activate && python3 setup.py --command-packages=stdeb.command bdist_deb'
      }
    }
  }

  post {
    always {
        cleanWs()
    }
  }
}
