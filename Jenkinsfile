pipeline {
  agent any

  stages {
    stage('Test') {
      steps{
        sh 'python3 -m venv env'
        dir('backend') {
          sh '. ../env/bin/activate && pip3 install -r requirements.txt && pylint_runner'
        }
      }
    }
  }

  post {
    always {
        cleanWs()
    }
  }
}
