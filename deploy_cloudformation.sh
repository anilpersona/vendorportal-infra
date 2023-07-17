#!/bin/bash

# http://blog.kablamo.org/2015/11/08/bash-tricks-eux/
set -euxo pipefail
cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
. "scripts/stack_name_vars.sh"

NONPRIV_ROLE_NAME='infra-cfnrole-vendorportal-nonprivileged'
PARAMS_FILE="cloudformation/params/${CFN_ENVIRONMENT}/${AWS_DEFAULT_REGION}.yml"

# shellcheck disable=SC1091

#enable when vault is enabled
. "scripts/vault_auth.sh"

{
# echo "Reading Postgres username from vault"
# CFN_REDIS_USERNAME=$(vault kv get -field=redis.rbac.user "kv2/prj/${VAULT_ENVIRONMENT}/${PROJECT_ID}/default")
# export CFN_REDIS_USERNAME

# CFN_REDIS_PWD=$(vault kv get -field=redis.rbac.password "kv2/prj/${VAULT_ENVIRONMENT}/${PROJECT_ID}/default")
# export CFN_REDIS_PWD


CFN_REDIS_AUTH_TOKEN=$(vault kv get -field=redis.auth.password "kv2/prj/${VAULT_ENVIRONMENT}/${PROJECT_ID}/default")
export CFN_REDIS_AUTH_TOKEN


# CFN_REDIS_DEFAULT_PWD=$(vault kv get -field=redis.rbac.default.password "kv2/prj/${VAULT_ENVIRONMENT}/${PROJECT_ID}/default")
# export CFN_REDIS_DEFAULT_PWD


# CFN_REDIS_DEFAULT_USERNAME=$(vault kv get -field=redis.rbac.default.user "kv2/prj/${VAULT_ENVIRONMENT}/${PROJECT_ID}/default")
# export CFN_REDIS_DEFAULT_USERNAME

CFN_DOCDB_MASTER_USER=$(vault kv get -field=docdb.masteruser "kv2/prj/${VAULT_ENVIRONMENT}/${PROJECT_ID}/default")
export CFN_DOCDB_MASTER_USER

CFN_DOCDB_MASTER_PWD=$(vault kv get -field=docdb.masterpwd "kv2/prj/${VAULT_ENVIRONMENT}/${PROJECT_ID}/default")
export CFN_DOCDB_MASTER_PWD

CFN_SUMO_ENDPOINT=$(vault kv get -field=sumo.collection.endpoint "kv2/prj/${VAULT_ENVIRONMENT}/${PROJECT_ID}/default")
export CFN_SUMO_ENDPOINT

SLACK_WEBHOOK=$(vault kv get -field=slack.incoming.webhook "kv2/prj/${VAULT_ENVIRONMENT}/${PROJECT_ID}/default")
CFN_SLACK_WEBHOOK=$(aws kms encrypt  --key-id "$CFN_KMS_KEY" \
                                    --plaintext fileb://<(echo -n "$SLACK_WEBHOOK") \
                                    --output text  \
                                    --query CiphertextBlob \
                                    --region "$AWS_DEFAULT_REGION" \
                                    --encryption-context env="$CFN_CONTEXT")
                                    #--plaintext "$SLACK_WEBHOOK" \ #enable when CLI v2 is installed
                                    # --cli-binary-format raw-in-base64-out \ #enable when CLI v2 is installed
                                    
export CFN_SLACK_WEBHOOK

} &> /dev/null

# get ssm params
# shellcheck disable=SC1091,SC2183
# . "scripts/export_roles.sh"

# shellcheck disable=SC1091,SC2183
. "scripts/export_roles_v2.sh"

# shellcheck disable=SC1091,SC2183
. "scripts/export_creds.sh"

cfn_manage deploy-stack \
  --stack-name "$CFN_SUMO_SHIP" \
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/sumo-ship.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME"

cfn_manage deploy-stack \
  --stack-name "$CFN_IAM_STACK" \
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/iam.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME"

cfn_manage deploy-stack \
  --stack-name "$CFN_KMS_STACK" \
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/kms.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME"

cfn_manage deploy-stack \
  --stack-name "$CFN_S3_STACK" \
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/s3.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME"

cfn_manage deploy-stack \
  --stack-name "$CFN_FRONTEND_STACK"\
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/deploy-frontend.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME"

cfn_manage deploy-stack \
    --stack-name "$CFN_SG_STACK" \
    --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/sg.yml" \
    --parameters-file "$PARAMS_FILE" \
    --role-name "$NONPRIV_ROLE_NAME"
cfn_manage deploy-stack \
    --stack-name "$CFN_ALB_STACK" \
    --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/alb.yml" \
    --parameters-file "$PARAMS_FILE" \
    --role-name "$NONPRIV_ROLE_NAME"

cfn_manage deploy-stack \
    --stack-name "$CFN_ALBSEC_STACK" \
    --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/alb_security.yml" \
    --parameters-file "$PARAMS_FILE" \
    --role-name "$NONPRIV_ROLE_NAME"

cfn_manage deploy-stack \
  --stack-name "$CFN_RELAY_STACK"\
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/relay.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME"

cfn_manage deploy-stack \
  --stack-name "$CFN_SNS_STACK"\
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/sns.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME"
cfn_manage deploy-stack \
  --stack-name "$CFN_ECS_NOTIFICATION"\
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/ecs-notification.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME"    
            # cfn_manage deploy-stack \
            #   --stack-name "$CFN_DYNAMO_PRODUCT_STACK"\
            #   --template-file 'cloudformation/templates/dynamodb-product.yml' \
            #   --parameters-file "$PARAMS_FILE" \
            #   --role-name "$NONPRIV_ROLE_NAME"

cfn_manage deploy-stack \
  --stack-name "$CFN_DYNAMO_OPVSAO_STACK" \
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/dynamodb-opvsao.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME"

cfn_manage deploy-stack \
  --stack-name "$CFN_DYNAMO_CMD_DOWNLOAD_STACK" \
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/dynamodb-cmd-download.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME"

cfn_manage deploy-stack \
  --stack-name "$CFN_REDIS_STACK"\
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/redis.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME"


cfn_manage deploy-stack \
  --stack-name "$CFN_REDIS_V2_STACK"\
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/redis_v2.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME" \


cfn_manage deploy-stack \
  --stack-name "$CFN_DOCDB_STACK"\
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/docdb.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME"

cfn_manage deploy-stack \
  --stack-name "$CFN_SUMO_STACK"\
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/sumologic_roles.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME"

cfn_manage deploy-stack \
  --stack-name "$CFN_SECROT_STACK"\
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/secret_rotation.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME"
  