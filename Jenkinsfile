pipeline {
  agent any

  stages {
    stage('Test') {
      steps{
        sh './dev-tools/install.sh'
        sh '. .venv/bin/activate && cd backend && pylint_runner'
        sh '. .venv/bin/activate && pip3 install stdeb && python3 setup.py --command-packages=stdeb.command bdist_deb'
      }
    }
  }

  post {
    always {
        cleanWs()
    }
  }
}
