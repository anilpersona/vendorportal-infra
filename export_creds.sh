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

#redis admin user
ADMIN_REDIS=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/admin/redis/credentials" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --with-decryption \
                          --output text \
                            --query "Parameter.Value")


CFN_REDIS_ADMIN_USERNAME=$(echo "$ADMIN_REDIS" | jq '.username' |  tr -d '"')
CFN_REDIS_ADMIN_PWD=$(echo "$ADMIN_REDIS" | jq '.password' |  tr -d '"')
CFN_REDIS_ADMIN_USERID=$(echo "$ADMIN_REDIS" | jq '.username' |  tr -d '"' | tr '[:upper:]' '[:lower:]')
export CFN_REDIS_ADMIN_USERID
export CFN_REDIS_ADMIN_USERNAME
export CFN_REDIS_ADMIN_PWD

#redis  osb user
OSB_REDIS=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/osb/redis/credentials" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --with-decryption \
                          --output text \
                            --query "Parameter.Value")


CFN_REDIS_OSB_USERNAME=$(echo "$OSB_REDIS" | jq '.username' |  tr -d '"')
CFN_REDIS_OSB_PWD=$(echo "$OSB_REDIS" | jq '.password' |  tr -d '"')
CFN_REDIS_OSB_USERID=$(echo "$OSB_REDIS" | jq '.username' |  tr -d '"' | tr '[:upper:]' '[:lower:]')
export CFN_REDIS_OSB_USERNAME
export CFN_REDIS_OSB_PWD
export CFN_REDIS_OSB_USERID

#redis sfrs user
SFRS_REDIS=$(aws ssm get-parameter \
                          --name "/${PROJECT_ID}/sfrs/redis/credentials" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --with-decryption \
                          --output text \
                            --query "Parameter.Value")


CFN_REDIS_SFRS_USERNAME=$(echo "$SFRS_REDIS" | jq '.username' |  tr -d '"')
CFN_REDIS_SFRS_PWD=$(echo "$SFRS_REDIS" | jq '.password' |  tr -d '"')
CFN_REDIS_SFRS_USERID=$(echo "$SFRS_REDIS" | jq '.username' |  tr -d '"' | tr '[:upper:]' '[:lower:]')
export CFN_REDIS_SFRS_USERID
export CFN_REDIS_SFRS_USERNAME
export CFN_REDIS_SFRS_PWD


#enable old values
export AWS_ACCESS_KEY_ID=$OLD_AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY=$OLD_AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN
