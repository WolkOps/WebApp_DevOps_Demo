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
      DOCKER_IMAGE_NAME       = "demo-webapp"
      DOCKER_IMAGE_VERSION    = "${BUILD_NUMBER}"
      PYTHONPATH              ="${WORKSPACE}:${PYTHONPATH}"
      SQLITE_DB_LOCATION      ="${WORKSPACE}/test-sqlite"
      SOS_SERVER_URL          = "http://a9e6ee97b031611e89b9102e3670d4d6-613919789.us-east-2.elb.amazonaws.com"
   }

   stages {

      stage('Unit Test') { // for display purposes
         steps {

            // Checkout code
            checkout([
               $class: 'GitSCM', 
               userRemoteConfigs: [[
                     url: 'https://github.com/WolkOps/WebApp_DevOps_Demo.git', 
                     name: 'origin',
                     refspec: ''
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
            nosetests --nologcapture --nocapture --verbose --with-xunit --xunit-file="./unit-nosetests.xml" --where="./tests";
            '''

            // Publish unit test results
            junit "${env.TEST_RESULT_LOCATION}"
         }         
      }

      /*
         How to build and push docker images to ECR:
         https://blog.mikesir87.io/2016/04/pushing-to-ecr-using-jenkins-pipeline-plugin/
      */
      stage('Build Docker Image') {
         steps {
            script{
               docker.build('${DOCKER_IMAGE_NAME}:${DOCKER_IMAGE_VERSION}')
               docker.build('${DOCKER_IMAGE_NAME}:latest')
            }
         }
      }

      stage('Push Docker Image') {
         steps {
            script {
               docker.withRegistry('https://956975823273.dkr.ecr.us-east-2.amazonaws.com', 'ecr:us-east-2:demo-ecr-credentials') {
                  docker.image('${DOCKER_IMAGE_NAME}').push('${DOCKER_IMAGE_VERSION}')
                  docker.image('${DOCKER_IMAGE_NAME}').push('latest')
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
               --parameter VERSION ${DOCKER_IMAGE_VERSION} \
               | kubectl apply -f -
            '''
         }
      }

      stage('Acceptance') {
         steps {
            sh '''
            #!/bin/bash
            set -e

            # Activate the virtual environment
            set +x; . "./venv/bin/activate"; set -x;

            # Install robotframework requirements
            pip install -q -r ./acceptance-tests/requirements.txt

            # Run robot framework
            robot ./acceptance-tests/robot-test.robot 
            '''

            step([
               $class : 'RobotPublisher',
               outputPath : "${WORKSPACE}",
               disableArchiveOutput : false,
               passThreshold : 100,
               unstableThreshold: 95.0,
               reportFileName   : 'report*.html',
               logFileName      : 'log*.html',
               outputFileName   : 'output*.xml',
               otherFiles : ""
            ])

         }
      }

      stage('Deploy to Prod') {
         steps {
            sh '''
            #!/bin/bash
            set -e

            # Run Deployment to Prod
            ktmpl ./deploy/sos-deployment-tmpl.yaml \
               --parameter NAMESPACE production \
               --parameter VERSION ${DOCKER_IMAGE_VERSION} \
               | kubectl apply -f -
            '''
         }
      }
   }

   post{
      always {
         // Print that pipeline is finished
         echo 'Pipeline done, recording results and cleaning up environment...'

         // deactivate and destroy VENV
         sh '''
         rm -fr ./venv/
         '''
      }
   }
}