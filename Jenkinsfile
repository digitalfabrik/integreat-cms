pipeline {
  agent any

  stages {
    stage('Test') {
      steps{
        sh 'python3 -m venv env'
        sh '. env/bin/activate && python3 setup.py develop && cd backend && pylint_runner'
        sh '. env/bin/activate && pip3 install stdeb'
        sh '. env/bin/activate && python3 setup.py --command-packages=stdeb.command bdist_deb'
      }
    }
  }

  post {
    always {
        cleanWs()
    }
  }
}
