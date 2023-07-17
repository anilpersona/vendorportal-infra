#!/usr/bin/env groovy
pipeline {
  agent any

  environment {
    AWS_DEFAULT_REGION = 'ap-southeast-2'
    //SLACK_NOTIFY_CHANNEL = "C021SU679T4"
    SLACK_NOTIFY_CHANNEL = "C020ES5TMNY"
    PROJECT_ID = 'vendorportal'
    RETAIN_BRANCH_DEPLOY = 'no' // retain branch deployment for dependent stacks
    CFN_BUILD_NUMBER="${env.BUILD_NUMBER}"
    CFN_BRANCH_NAME =  sh (
      script: "echo ${env.BRANCH_NAME} | sed -r 's/[/]/_/g'",
      returnStdout: true
    ).trim()
    CFN_TEMPLATE_DIR="cloudformation/templates/"
  }

  options {
    disableConcurrentBuilds()
  }

  stages {
    stage('Upload CFN artefacts to S3 Dev') {
      when {
        expression {
          return BRANCH_NAME =~ 'develop|hotfix.*|feature.*'
        }
      }
      environment {
        CFN_ENVIRONMENT = 'dev'
        AWS_DEFAULT_REGION = 'ap-southeast-2'
        CFN_ARTIFACT_BUCKET = "kmartau-vendorportal-artifact-${env.CFN_ENVIRONMENT}"
      }
      steps {
        script {
          node {
            uploadCfnArtifacts()
          }
        }
      }
    }
    stage ('Parallel Linting') {
      when {
        expression {
          return BRANCH_NAME =~ 'develop|hotfix.*|feature.*'
        }
      }
      environment {
        ENVIRONMENT = 'dev'
        CFN_ENVIRONMENT="${env.ENVIRONMENT}"
        CFN_ARTIFACT_BUCKET = "kmartau-vendorportal-artifact-${env.CFN_ENVIRONMENT}"
      }
      steps {
        script {
          node {
            deleteDir()
            checkout scm
            def builds = [:]
            builds['shellcheck'] = {
              ->
                docker.image("${ECR_HOST}/sharedtools/shellcheck:latest").inside {
                sh 'chmod +x scripts/shellcheck.sh'
                sh './scripts/shellcheck.sh'
              }
            }
            builds['jenkinsfile'] = {
              ->
                docker.image("${ECR_HOST}/sharedtools/astyle:latest").inside {
                sh 'chmod +x scripts/jenkinsfile_beautify.sh'
                sh './scripts/jenkinsfile_beautify.sh'
              }
            }
            builds['cloudformation'] = {
              ->
                docker.image("${ECR_HOST}/sharedtools/cfn_manage:latest").inside {
                sh 'chmod +x scripts/cfn_validate.sh'
                sh './scripts/cfn_validate.sh'
              }
            }
            withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: "${env.PROJECT_ID}-aws-${env.ENVIRONMENT}"]]) {
              parallel builds
            }
          }
        }
      }
    }
    stage('Upload CFN artefact to s3 - Artifacts') {
      when {
        expression {
          return BRANCH_NAME =~ 'master|main|develop|hotfix.*|release.*|feature.*'
        }
      }
      environment {
        CFN_ENVIRONMENT = 'artefact'
        AWS_DEFAULT_REGION = 'ap-southeast-2'
        CFN_ARTIFACT_BUCKET = "kmartau-vendorportal-artefacts"
        TIMESTAMP =  sh (script: 'date -u +"%Y-%m-%d_%H-%M-%S"',returnStdout: true).trim()
      }
      steps {
        script {
          node {
            checkout scm
            withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]]) {
              docker.image("${ECR_HOST}/sharedtools/cfn_manage:latest").inside {
                sh "aws s3 cp cloudformation s3://${env.CFN_ARTIFACT_BUCKET}/infra/cloudformation/${env.CFN_BRANCH_NAME}-${env.CFN_BUILD_NUMBER}/ --recursive --sse"
              }
            }
          }
        }
      }
    }
    stage('Deploy Artefacts: ECR') {
      when {
        expression {
          return BRANCH_NAME =~ 'main|develop|hotfix.*|release.*|feature.*'
        }
      }
      environment {
        CFN_ENVIRONMENT = 'artefact'
        AWS_DEFAULT_REGION = 'ap-southeast-2'
        CFN_ARTIFACT_BUCKET = "kmartau-vendorportal-artefacts"
        TIMESTAMP =  sh (script: 'date -u +"%Y-%m-%d_%H-%M-%S"',returnStdout: true).trim()
      }
      steps {
        script {
          node {
            checkout scm
            withCredentials([
                              [$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]
                            ]) {
              docker.image("${ECR_HOST}/sharedtools/cfn_manage:latest").inside {
                sh 'chmod +x scripts/create_artefact.sh'
                sh 'scripts/create_artefact.sh'
              }
            }
          }
        }
      }
    }
    stage('Deploy s3 Buckets dev') {
      when {
        expression {
          return BRANCH_NAME =~ 'develop|feature.*'
        }
      }
      environment {
        CFN_AWS_ACC='187628286232'
        CFN_KMS_KEY='626af879-23ba-4708-868f-0b7c551352cc'
        CFN_ENVIRONMENT = 'dev'
        CFN_ARTIFACT_BUCKET = "kmartau-vendorportal-artifact-${env.CFN_ENVIRONMENT}"
        CFN_PROJECT = "${env.PROJECT_ID}"
        VAULT_ENVIRONMENT = "dev"
        TIMESTAMP =  sh (script: 'date -u +"%Y-%m-%d_%H-%M-%S"',returnStdout: true).trim()
      }
      steps {
        script {
          node {
            checkout scm
            withCredentials([
                              [$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]
                            ]) {
              docker.image("${ECR_HOST}/sharedtools/cfn_manage:latest").inside {
                sh "aws sts get-caller-identity"
                deployS3Cft()
              }
            }
          }
        }
      }
    }
    stage('Deploy DEV us-east-1') {
      when {
        expression {
          return BRANCH_NAME =~ 'develop|feature.*'
        }
      }
      environment {
        CFN_AWS_ACC='187628286232'
        CFN_ENVIRONMENT = "dev"
        VAULT_ENVIRONMENT = "dev"
        AWS_DEFAULT_REGION ="us-east-1"
        CFN_PROJECT = "${env.PROJECT_ID}"
        // CFN_KMS_KEY='626af879-23ba-4708-868f-0b7c551352cc'
        CFN_ARTIFACT_BUCKET = "kmartau-vendorportal-artifact-${env.CFN_ENVIRONMENT}"
        CFN_EDGE_ARTIFACT_BUCKET = "kmartau-vendorportal-edge-artifact-${env.CFN_ENVIRONMENT}"
        TIMESTAMP =  sh (script: 'date -u +"%Y-%m-%d_%H-%M-%S"',returnStdout: true).trim()
      }
      steps {
        script {
          node {
            deleteDir()
            checkout scm
            withEnv(["http_proxy=proxy.int.sharedsvc.a-sharedinfra.net:8080"]) {
              withEnv(["https_proxy=proxy.int.sharedsvc.a-sharedinfra.net:8080"]) {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]]) {
                  uploadLambdas('edge_lambdas','${CFN_EDGE_ARTIFACT_BUCKET}')
                  uploadSumoZipToKmart('sumo/cloudwatchlogs-with-dlq.zip','${CFN_EDGE_ARTIFACT_BUCKET}')
                }
              }
            }
            withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]]) {
              docker.image("${ECR_HOST}/sharedtools/cfn_manage:latest").inside {
                deployEdgeBucket()
                deployRegionalCft()
                deploy_lambda_version('edge_lambdas')
              }
            }
          }
        }
      }
    }
    stage('Deploy to Dev') {
      when {
        expression {
          return BRANCH_NAME =~ 'develop|feature.*'
        }
      }
      environment {
        CFN_AWS_ACC='187628286232'
        CFN_KMS_KEY='626af879-23ba-4708-868f-0b7c551352cc'
        CFN_ENVIRONMENT = 'dev'
        VAULT_ENVIRONMENT = "dev"
        CFN_PROJECT = "${env.PROJECT_ID}"
        CFN_ARTIFACT_BUCKET = "kmartau-vendorportal-artifact-${env.CFN_ENVIRONMENT}"
        TIMESTAMP =  sh (script: 'date -u +"%Y-%m-%d_%H-%M-%S"',returnStdout: true).trim()
      }
      steps {
        script {
          node {
            deleteDir()
            checkout scm
            withEnv(["http_proxy=proxy.int.sharedsvc.a-sharedinfra.net:8080"]) {
              withEnv(["https_proxy=proxy.int.sharedsvc.a-sharedinfra.net:8080"]) {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]]) {
                  // sh "chmod +x scripts/export_roles_v2.sh"
                  // sh "scripts/export_roles_v2.sh"
                  // error("Test done, getting out")
                  uploadLambdas('lambdas','${CFN_ARTIFACT_BUCKET}')
                }
              }
            }
            withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]]) {
              docker.image("${ECR_HOST}/sharedtools/cfn_manage:latest").inside {
                uploadSumoZipToKmart('sumo/cloudwatchlogs-with-dlq.zip','${CFN_ARTIFACT_BUCKET}')
                deployCft()
              }
            }
          }
        }
      }
    }
    stage('Approval to nonprod') {
      when {
        expression {
          return BRANCH_NAME =~ 'release.*'
        }
      }
      environment {
        CFN_PROJECT_ID = "${env.PROJECT_ID}"
        CFN_ENVIRONMENT =  'nonprod'
      }
      steps {
        slackSend(
          color: "good",
          channel: "${env.SLACK_NOTIFY_CHANNEL}",
          message: "@here: <${env.JOB_DISPLAY_URL}|${env.JOB_NAME} #${env.BUILD_NUMBER}> Deploy to ${CFN_ENVIRONMENT}?  :zombiewalk:"
        )
        timeout(time: 3, unit: 'HOURS') {
          input message: "Deploy to ${CFN_ENVIRONMENT}?"
        }
      }
    }
    stage('Upload CFN artefact to s3 NP') {
      when {
        expression {
          return BRANCH_NAME =~ 'release.*'
        }
      }
      environment {
        CFN_ENVIRONMENT = 'nonprod'
        AWS_DEFAULT_REGION = 'ap-southeast-2'
        CFN_ARTIFACT_BUCKET = "kmartau-vendorportal-artifact-${env.CFN_ENVIRONMENT}"
      }
      steps {
        script {
          node {
            uploadCfnArtifacts()
          }
        }
      }
    }
    stage('Deploy s3 Buckets nonprod') {
      when {
        expression {
          return BRANCH_NAME =~ 'release.*'
        }
      }
      environment {
        CFN_AWS_ACC='318263296841'
        CFN_KMS_KEY='c361f9b4-7c47-4b60-80be-648bfe3bc87f'
        CFN_ENVIRONMENT = 'nonprod'
        CFN_ARTIFACT_BUCKET = "kmartau-vendorportal-artifact-${env.CFN_ENVIRONMENT}"
        CFN_PROJECT = "${env.PROJECT_ID}"
        VAULT_ENVIRONMENT = "nonprod"
        TIMESTAMP =  sh (script: 'date -u +"%Y-%m-%d_%H-%M-%S"',returnStdout: true).trim()
      }
      steps {
        script {
          node {
            checkout scm
            withCredentials([
                              [$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]
                            ]) {
              docker.image("${ECR_HOST}/sharedtools/cfn_manage:latest").inside {
                sh "aws sts get-caller-identity"
                deployS3Cft()
              }
            }
          }
        }
      }
    }
    stage('Deploy nonprod us-east-1') {
      when {
        expression {
          return BRANCH_NAME =~ 'release.*'
        }
      }
      environment {
        CFN_AWS_ACC='318263296841'
        CFN_ENVIRONMENT = 'nonprod'
        VAULT_ENVIRONMENT = "nonprod"
        AWS_DEFAULT_REGION ='us-east-1'
        CFN_PROJECT = "${env.PROJECT_ID}"
        // CFN_KMS_KEY='c361f9b4-7c47-4b60-80be-648bfe3bc87f'
        CFN_ARTIFACT_BUCKET = "kmartau-vendorportal-artifact-${env.CFN_ENVIRONMENT}"
        CFN_EDGE_ARTIFACT_BUCKET = "kmartau-vendorportal-edge-artifact-${env.CFN_ENVIRONMENT}"
        TIMESTAMP =  sh (script: 'date -u +"%Y-%m-%d_%H-%M-%S"',returnStdout: true).trim()
      }
      steps {
        script {
          node {
            deleteDir()
            checkout scm
            withEnv(["http_proxy=proxy.int.sharedsvc.a-sharedinfra.net:8080"]) {
              withEnv(["https_proxy=proxy.int.sharedsvc.a-sharedinfra.net:8080"]) {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]]) {
                  uploadLambdas('edge_lambdas','${CFN_EDGE_ARTIFACT_BUCKET}')
                  uploadSumoZipToKmart('sumo/cloudwatchlogs-with-dlq.zip','${CFN_EDGE_ARTIFACT_BUCKET}')
                }
              }
            }
            withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]]) {
              docker.image("${ECR_HOST}/sharedtools/cfn_manage:latest").inside {
                deployEdgeBucket()
                deployRegionalCft()
                deploy_lambda_version('edge_lambdas')
              }
            }
          }
        }
      }
    }
    stage('Deploy Nonprod') {
      when {
        expression {
          return BRANCH_NAME =~ 'release.*'
        }
      }
      environment {
        CFN_AWS_ACC='318263296841'
        CFN_KMS_KEY='c361f9b4-7c47-4b60-80be-648bfe3bc87f'
        CFN_ENVIRONMENT = 'nonprod'
        CFN_PROJECT = "${env.PROJECT_ID}"
        VAULT_ENVIRONMENT = "nonprod"
        CFN_ARTIFACT_BUCKET = "kmartau-vendorportal-artifact-${env.CFN_ENVIRONMENT}"
        TIMESTAMP =  sh (script: 'date -u +"%Y-%m-%d_%H-%M-%S"',returnStdout: true).trim()
      }
      steps {
        script {
          node {
            deleteDir()
            checkout scm
            withEnv(["http_proxy=proxy.int.sharedsvc.a-sharedinfra.net:8080"]) {
              withEnv(["https_proxy=proxy.int.sharedsvc.a-sharedinfra.net:8080"]) {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]]) {
                  uploadLambdas('lambdas','${CFN_ARTIFACT_BUCKET}')
                }
              }
            }
            withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]]) {
              docker.image("${ECR_HOST}/sharedtools/cfn_manage:latest").inside {
                uploadSumoZipToKmart('sumo/cloudwatchlogs-with-dlq.zip','${CFN_ARTIFACT_BUCKET}')
                deployCft()
              }
            }
          }
        }
      }
    }
    stage('Approval to prod') {
      when {
        expression {
          return BRANCH_NAME =~ 'main|hotfix.*'
        }
      }
      environment {
        CFN_PROJECT_ID = "${env.PROJECT_ID}"
        CFN_ENVIRONMENT =  'prod'
      }
      steps {
        slackSend(
          color: "good",
          channel: "${env.SLACK_NOTIFY_CHANNEL}",
          message: "@here: <${env.JOB_DISPLAY_URL}|${env.JOB_NAME} #${env.BUILD_NUMBER}> Deploy to ${CFN_ENVIRONMENT}?  :zombiewalk:"
        )
        timeout(time: 3, unit: 'HOURS') {
          input message: "Deploy to ${CFN_ENVIRONMENT}?"
        }
      }
    }
    stage('Upload CFN artefact to s3 : Prod') {
      when {
        expression {
          return BRANCH_NAME =~ 'main|hotfix.*'
        }
      }
      environment {
        CFN_ENVIRONMENT = 'prod'
        AWS_DEFAULT_REGION = 'ap-southeast-2'
        CFN_ARTIFACT_BUCKET = "kmartau-vendorportal-artifact-${env.CFN_ENVIRONMENT}"
      }
      steps {
        script {
          node {
            uploadCfnArtifacts()
          }
        }
      }
    }
    stage('Deploy s3 Buckets production') {
      when {
        expression {
          return BRANCH_NAME =~ 'main|hotfix.*'
        }
      }
      environment {
        CFN_AWS_ACC='563000599290'
        CFN_KMS_KEY= 'a47d4bb5-02c2-43f4-a402-90c7232c82d0'
        CFN_ENVIRONMENT = 'prod'
        CFN_ARTIFACT_BUCKET = "kmartau-vendorportal-artifact-${env.CFN_ENVIRONMENT}"
        CFN_PROJECT = "${env.PROJECT_ID}"
        VAULT_ENVIRONMENT = "prod"
        TIMESTAMP =  sh (script: 'date -u +"%Y-%m-%d_%H-%M-%S"',returnStdout: true).trim()
      }
      steps {
        script {
          node {
            checkout scm
            withCredentials([
                              [$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]
                            ]) {
              docker.image("${ECR_HOST}/sharedtools/cfn_manage:latest").inside {
                sh "aws sts get-caller-identity"
                deployS3Cft()
              }
            }
          }
        }
      }
    }
    stage('Deploy production us-east-1') {
      when {
        expression {
          return BRANCH_NAME =~ 'main|hotfix.*'
        }
      }
      environment {
        CFN_AWS_ACC='563000599290'
        CFN_ENVIRONMENT = 'prod'
        VAULT_ENVIRONMENT = "prod"
        AWS_DEFAULT_REGION ='us-east-1'
        CFN_PROJECT = "${env.PROJECT_ID}"
        // CFN_KMS_KEY= 'a47d4bb5-02c2-43f4-a402-90c7232c82d0'
        CFN_ARTIFACT_BUCKET = "kmartau-vendorportal-artifact-${env.CFN_ENVIRONMENT}"
        CFN_EDGE_ARTIFACT_BUCKET = "kmartau-vendorportal-edge-artifact-${env.CFN_ENVIRONMENT}"
        TIMESTAMP =  sh (script: 'date -u +"%Y-%m-%d_%H-%M-%S"',returnStdout: true).trim()
      }
      steps {
        script {
          node {
            deleteDir()
            checkout scm
            withEnv(["http_proxy=proxy.int.sharedsvc.a-sharedinfra.net:8080"]) {
              withEnv(["https_proxy=proxy.int.sharedsvc.a-sharedinfra.net:8080"]) {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]]) {
                  uploadLambdas('edge_lambdas','${CFN_EDGE_ARTIFACT_BUCKET}')
                  uploadSumoZipToKmart('sumo/cloudwatchlogs-with-dlq.zip','${CFN_EDGE_ARTIFACT_BUCKET}')
                }
              }
            }
            withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]]) {
              docker.image("${ECR_HOST}/sharedtools/cfn_manage:latest").inside {
                deployEdgeBucket()
                deployRegionalCft()
                deploy_lambda_version('edge_lambdas')
              }
            }
          }
        }
      }
    }
    stage('Deploy production') {
      when {
        expression {
          return BRANCH_NAME =~ 'main|hotfix.*'
        }
      }
      environment {
        CFN_AWS_ACC='563000599290'
        CFN_KMS_KEY= 'a47d4bb5-02c2-43f4-a402-90c7232c82d0'
        CFN_ENVIRONMENT = 'prod'
        CFN_PROJECT = "${env.PROJECT_ID}"
        VAULT_ENVIRONMENT = "prod"
        CFN_ARTIFACT_BUCKET = "kmartau-vendorportal-artifact-${env.CFN_ENVIRONMENT}"
        TIMESTAMP =  sh (script: 'date -u +"%Y-%m-%d_%H-%M-%S"',returnStdout: true).trim()
      }
      steps {
        script {
          node {
            deleteDir()
            checkout scm
            withEnv(["http_proxy=proxy.int.sharedsvc.a-sharedinfra.net:8080"]) {
              withEnv(["https_proxy=proxy.int.sharedsvc.a-sharedinfra.net:8080"]) {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]]) {
                  uploadLambdas('lambdas','${CFN_ARTIFACT_BUCKET}')
                }
              }
            }
            withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]]) {
              docker.image("${ECR_HOST}/sharedtools/cfn_manage:latest").inside {
                uploadSumoZipToKmart('sumo/cloudwatchlogs-with-dlq.zip','${CFN_ARTIFACT_BUCKET}')
                deployCft()
              }
            }
          }
        }
      }
    }
  }
  post {
    always {
      script {
        if (BRANCH_NAME == 'main') {
          CALLOUT = '@here '
        } else {
          CALLOUT = ''
        }
      }
    }
    success {
      slackSend(
        color: 'good',
        channel: SLACK_NOTIFY_CHANNEL,
        message: ":green_tick: SUCCESS: Job - <${env.JOB_DISPLAY_URL}|${env.JOB_NAME} #${env.BUILD_NUMBER}>"
      )
    }
    failure {
      slackSend(
        color: 'danger',
        channel: SLACK_NOTIFY_CHANNEL,
        message: "${CALLOUT}:red_cross: FAILURE: Job - <${env.JOB_DISPLAY_URL}|${env.JOB_NAME} #${env.BUILD_NUMBER}>"
      )
    }
    unstable {
      slackSend(
        color: 'warning',
        channel: SLACK_NOTIFY_CHANNEL,
        message: "${CALLOUT} UNSTABLE: Job - <${env.JOB_DISPLAY_URL}|${env.JOB_NAME} #${env.BUILD_NUMBER}>"
      )
    }
    aborted {
      slackSend(
        color: 'warning',
        channel: SLACK_NOTIFY_CHANNEL,
        message: "${CALLOUT}:black_circle: ABORTED: Job - <${env.JOB_DISPLAY_URL}|${env.JOB_NAME} #${env.BUILD_NUMBER}>"
      )
    }
  }
}

def deployCft() {
  String ecs_stack_name= "vendorportal-stack-ecs-${CFN_ENVIRONMENT}";
  sh "chmod +x scripts/deploy_cloudformation.sh"
  sh "scripts/deploy_cloudformation.sh"
  // sh "chmod +x scripts/python/update_frontend_s3.py"  //enable once UI changes goes to Prod
  // sh "python3 scripts/python/update_frontend_s3.py '${CFN_ENVIRONMENT}' 'osb/'" //enable once UI changes goes to Prod
  // sh "python3 scripts/python/update_frontend_s3.py '${CFN_ENVIRONMENT}' 'landing-page/'" //enable once UI changes goes to Prod
}
def deployS3Cft() {
  // println("pass")
  sh "chmod +x scripts/deploy_s3_buckets.sh" //enable once IAM is updated
  sh "scripts/deploy_s3_buckets.sh" //enable once IAM is updated
}
def deployRegionalCft() {
  sh "chmod +x scripts/deploy_region.sh"
  sh "scripts/deploy_region.sh"
  sh "python3 ./scripts/python/update_waf_logconfig.py ${CFN_ENVIRONMENT} ${CFN_PROJECT}"
  sh "python3 ./scripts/python/create_webacl_ssm.py ${CFN_ENVIRONMENT} ${CFN_PROJECT}"
}
def deployEdgeBucket() {
  sh "chmod +x scripts/deploy_edge_bucket.sh"
  sh "scripts/deploy_edge_bucket.sh"
}
def uploadLambdas(path,bucket) {
  dir(path) {
    def files = findFiles();
    files.each { file ->
    try {
      println("${file}");
      if( file.directory ) {
        directoryName=file.toString();
        dir(directoryName) {
          List<String> lfiles = sh(script: "ls", returnStdout: true).split();
          lfiles.each { item ->
          try {
            if(item.split('\\.')[1] == "py") {
              println("${item}");
              lambda_prefix = item.split('\\.')[0];
              sh "cp ${item} ./lambda_function.py"
              sh "mkdir packages"
              docker.image("${ECR_HOST}/vendorportal/pythonsdk-aws:latest").inside {
                sh "python3 -m pip install --target ./packages -r requirements.txt"
                dir("packages") {
                  sh "zip -r ../${env.TIMESTAMP}.zip ."
                }
                sh "zip -g ${env.TIMESTAMP}.zip ./lambda_function.py ./kmart.pem ./rds.pem"
              }
              sh "aws s3 cp ${env.TIMESTAMP}.zip s3://${bucket}/infra/lambda/${lambda_prefix}/ --sse"
              sh "rm -rf packages ${env.TIMESTAMP}.zip ./lambda_function.py"
              return
            } else if(item.split('\\.')[1] == "js") {
              println("${item}");
              lambda_prefix = item.split('\\.')[0];
              sh "cp ${item} ./lambda_function.js"
              sh "zip -g ${env.TIMESTAMP}.zip ./lambda_function.js"
              sh "aws s3 cp ${env.TIMESTAMP}.zip s3://${bucket}/infra/lambda/${lambda_prefix}/ --sse"
              sh "rm -rf packages ${env.TIMESTAMP}.zip ./lambda_function.js"
              return
            } else {
              println("next file")
            }
          } catch(Exception e) {
            println(e)
            sh "exit 1"
          }
                      }
        }
      }
    } catch(Exception e) {
      println(e);
      sh "exit 1"
    }
               }
  }
}

def listLambdaName(filename) {
  String lambda_name;
  if(filename == 'origin_request.js') {
    lambda_name='vendorportal-edge-origin-request-lambda'
  } else if(filename == 'origin_response.js') {
    lambda_name='vendorportal-edge-origin-response'
  } else {
    lambda_name=''
  }
  return lambda_name
}

def deploy_lambda_version(path) {
  dir(path) {
    def dirs = findFiles();
    dirs.each { file ->
    try {
      println("${file}");
      if( file.directory ) {
        directoryName=file.toString();
        dir(directoryName) {
          List<String> files = sh(script: "ls", returnStdout: true).split();
          Map<String,String> fnData = [:];
          files.each { item ->
          try {
            println("${item}");
            res = sh(script: "bash ../../scripts/get_diff.sh '${item}'", returnStdout: true);
            lambda_name = listLambdaName(item);
            if(lambda_name != '') {
              fnData=[
                       "aws_env": "${env.CFN_ENVIRONMENT}",
                       "region": "${env.AWS_DEFAULT_REGION}",
                       "lambda_name": "${lambda_name}",
                       "publish": "${res}"
                     ];
              sh "chmod +x ../../scripts/python/deploy_lambda_version.py"
              sh "python3 ../../scripts/python/deploy_lambda_version.py '${fnData}'"
            } else {
              println("Lambda does not need deployment")
            }
          } catch(Exception e) {
            println(e)
            sh "exit 1"
          }
                     }
        }
      }
    } catch(Exception e) {
      println(e)
      sh "exit 1"
    }
              }
  }
}
def uploadSumoZipToKmart(file,bucket) {
  sh "curl https://appdevzipfiles-ap-southeast-2.s3.ap-southeast-2.amazonaws.com/cloudwatchlogs-with-dlq.zip \
      --output cloudwatchlogs-with-dlq.zip"
  sh "ls -lart"
  sh "aws s3 cp cloudwatchlogs-with-dlq.zip s3://${bucket}/sumo/ --sse"
}

def uploadCfnArtifacts() {
  checkout scm;
  withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',credentialsId: "${env.PROJECT_ID}-aws-${env.CFN_ENVIRONMENT}"]]) {
    docker.image("${ECR_HOST}/sharedtools/cfn_manage:latest").inside {
      sh "aws s3 cp cloudformation s3://${env.CFN_ARTIFACT_BUCKET}/infra/cloudformation/${env.CFN_BRANCH_NAME}-${env.CFN_BUILD_NUMBER}/ --recursive --sse"
    }
  }
}
