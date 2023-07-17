#!/bin/bash

# exit when any command fails
set -e

#preserve old values
OLD_AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
OLD_AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY

# shellcheck disable=SC2183,SC2046,SC2086
export $(printf "AWS_ACCESS_KEY_ID=%s AWS_SECRET_ACCESS_KEY=%s AWS_SESSION_TOKEN=%s" \
$(aws sts assume-role \
--role-arn arn:aws:iam::${CFN_AWS_ACC}:role/infra-cfnrole-${PROJECT_ID}-nonprivileged \
--role-session-name infra-prjauth-vendorportal \
--query "Credentials.[AccessKeyId,SecretAccessKey,SessionToken]" \
--output text))

#step function soh
CFN_LAMBDA_ROLE_SOH_STEP_SCH=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/iam-role-arn/sohstepfn-scheduler" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_SOH_STEP_SCH
#step function ssm change notify lambda role
CFN_LAMBDA_ROLE_STEP_SOH_SSM_CHANGE=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/iam-role-arn/sohstepfn-ssm-change-notify" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_STEP_SOH_SSM_CHANGE

#step function ssm soh publish data lambda role
CFN_LAMBDA_ROLE_SOH_DATA_PUBLISH=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/soh-data-publisher-lambda" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_SOH_DATA_PUBLISH

#lambda function ssm ordercomparison lambda role
CFN_LAMBDA_ROLE_OPVSAO_INITIATOR=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/opvsao-report-initiator" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_OPVSAO_INITIATOR

#lambda function ssm ordercomparison lambda role
CFN_LAMBDA_ROLE_OPVSAO_BUILDER=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/opvsao-report-builder" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_OPVSAO_BUILDER

#lambda function ssm supplier invitation lambda role
CFN_LAMBDA_ROLE_SUPPLIER_INVITATION=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/supplier-invitation" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_SUPPLIER_INVITATION

#ecs ssm factory api role
CFN_ECS_ROLE_FACTORY_API=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/ecs/iam-role-arn/factory" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_ECS_ROLE_FACTORY_API

#ecs ssm factory api role
CFN_ECS_ROLE_SUPPLIER_API=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/ecs/iam-role-arn/supplier" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_ECS_ROLE_SUPPLIER_API

#lambda function ssm apparel commitment data handler lambda role
CFN_LAMBDA_ROLE_APP_COMMITMENT_HANDLER=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/commitmentdata-handler" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_APP_COMMITMENT_HANDLER

#ecs ssm commitmentdata api role
CFN_ECS_ROLE_COMMITMENT_DATA_API=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/ecs/iam-role-arn/commitment-data" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_ECS_ROLE_COMMITMENT_DATA_API

#lambda function ssm supplier registration lambda role
CFN_LAMBDA_ROLE_SUPPLIER_EVENT=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/supplier-event-publisher" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_SUPPLIER_EVENT

#lambda function ssm factory event publisher lambda role
CFN_LAMBDA_ROLE_FACTORY_EVENT_PUBLISH=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/factory-event-publisher" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_FACTORY_EVENT_PUBLISH


#lambda function ssm soh historical data push lambda role
CFN_LAMBDA_ROLE_SOH_HISTORICAL_DATA_PUSH=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/soh-historical-data-push" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_SOH_HISTORICAL_DATA_PUSH

#lambda function ssm ecs notify lambda role
CFN_LAMBDA_ROLE_ECS_NOTIFY=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/ecs-notify" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_ECS_NOTIFY


#lambda function ssm commitmentdata handler lambda role
CFN_LAMBDA_ROLE_COMMITMENTDATA_EXPORT=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/commitmentdata-export-handler" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_COMMITMENTDATA_EXPORT

#ecs supplier registration api role
CFN_ECS_ROLE_SUPPLIER_REGISTRATION=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/ecs/iam-role-arn/supplier-registration" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_ECS_ROLE_SUPPLIER_REGISTRATION

#step function soh
CFN_LAMBDA_ROLE_SOH_STEP=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/soh-step-lambda" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_SOH_STEP

#lambda function ssm ordercomparison lambda role - new
CFN_LAMBDA_ROLE_OPVSAO_INITIATOR_V2=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/opvsao-initiator-lambda" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_OPVSAO_INITIATOR_V2

#lambda function ssm ordercomparison lambda role - new 
CFN_LAMBDA_ROLE_OPVSAO_BUILDER_V2=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/opvsao-reportbuilder-lambda" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_OPVSAO_BUILDER_V2

#lambda function ssm secret rotation lambda role - new 
CFN_LAMBDA_ROLE_SECROT=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/secrot" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_SECROT

#lambda function ssm secret rotation lambda role - new 
CFN_LAMBDA_ROLE_IAM_SYNC=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/identity-management-sync" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_IAM_SYNC
#step function soh
CFN_SUMO_LOG_SHIPPER_LAMBDA_ARN=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/sumo/lambda/arn" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_SUMO_LOG_SHIPPER_LAMBDA_ARN

#lambda function ssm sfrs notification lambda role
CFN_LAMBDA_ROLE_SFRS_FACTORY_NOTIFY=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/sfrs-factory-notification" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_SFRS_FACTORY_NOTIFY


#lambda function ssm sfrs notification lambda role
CFN_LAMBDA_ROLE_SFRS_SUPPLIER_NOTIFY=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/lambda/iam-role-arn/sfrs-supplier-notification" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameter.Value" \
                          --output text || echo -n "")
export CFN_LAMBDA_ROLE_SFRS_SUPPLIER_NOTIFY

#enable old values
export AWS_ACCESS_KEY_ID=$OLD_AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY=$OLD_AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN
