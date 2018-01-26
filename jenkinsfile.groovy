#!groovy

pipeline {
   agent {
      node {
         label 'master'
      }
   }

   parameters {
      string(name: 'ghprbActualCommit', defaultValue: 'master', description: 'When starting build give the sha1 parameter commit id you want to build or refname (eg: origin/pr/9/head).')
   }

   environment {
      TEST_RESULT_LOCATION    = "**/*-nosetests.xml"
      SSH_CONFIG_BASE         = "/var/lib/jenkins/.ssh/config.d/${env.BUILD_TAG}"
      DOCKER_IMAGE_NAME       = "demo-webapp"
      DOCKER_IMAGE_VERSION    = "latest"
      PYTHONPATH              ="${WORKSPACE}:${PYTHONPATH}"
      SQLITE_DB_LOCATION      ="${WORKSPACE}/test-sqlite"
   }

   stages {

      stage('Unit Test') { // for display purposes
         steps {

            // Checkout code
            checkout([
               $class: 'GitSCM', 
               userRemoteConfigs: [[
                     url: 'https://github.com/WolkOps/WebApp_DevOps_Demo.git', 
                     name: 'origin'
               ]],
               branches: [[name: "${params.ghprbActualCommit}"]],
               extensions: [
                  [$class: 'WipeWorkspace'] // wipe workspace before clone
               ]
             ])

            sh '''
            #!/bin/bash
            set -e

            # Create and activate virtual environment
            virtualenv ./venv
            set +x; . "./venv/bin/activate"; set -x;

            # Install requirements
            pip install -q -r requirements.txt

            # Run unit tests
            nosetests --nologcapture --nocapture --verbose --with-xunit --xunit-file="./unit-nosetests.xml" --where="./test";
            '''
         }         
      }

      stage('Build Docker Image') {
         steps {
            script{
               docker.build('${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_VERSION}')
            }
         }
      }

      stage('Push Docker Image') {
         steps {
            script {
               docker.withRegistry('https://956975823273.dkr.ecr.us-east-2.amazonaws.com', 'ecr:us-east-2:demo-ecr-credentials') {
                  docker.image('${DOCKER_IMAGE_NAME}').push('${DOCKER_IMAGE_VERSION}')
               }
            }
         }
      }

      stage('Deploy to Test') {
         steps {
            sh '''
            #!/bin/bash
            set -e

            # Run Deployment to Test
            ktmpl ./deploy/sos-deployment-tmpl.yaml \
               --parameter NAMESPACE test \
               --parameter VERSION latest \
               | kubectl apply -f -
            '''
         }
      }

      stage('Acceptance') {
         steps {
            sh '''
            #!/bin/bash
            set -e

            # Run robot framework
            '''
         }
      }

      stage('Deploy to Prod') {
         steps {
            sh '''
            #!/bin/bash
            set -e

            # Run Deployment to Prod
            tmpl ./deploy/sos-deployment-tmpl.yaml \
               --parameter NAMESPACE production \
               --parameter VERSION latest \
               | kubectl apply -f -
            '''
         }
      }
   }

   post{
      always {
         // Print that pipeline is finished
         echo 'Pipeline done, recording results and cleaning up environment...'

         // Test Results
         junit "${env.TEST_RESULT_LOCATION}"

         // deactivate and destroy VENV
         sh '''
         rm -fr ./venv/
         '''
      }
   }
}