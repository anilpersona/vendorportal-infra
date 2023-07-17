#!/bin/bash

# http://blog.kablamo.org/2015/11/08/bash-tricks-eux/
set -euxo pipefail
cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
. "scripts/stack_name_vars.sh"

# get ssm params
# shellcheck disable=SC1091,SC2183
# . "scripts/export_roles.sh"

# shellcheck disable=SC1091,SC2183
. "scripts/export_roles_v2.sh"

NONPRIV_ROLE_NAME='infra-cfnrole-vendorportal-nonprivileged'
PARAMS_FILE="cloudformation/params/${CFN_ENVIRONMENT}/${AWS_DEFAULT_REGION}.yml"
echo "$NONPRIV_ROLE_NAME $PARAMS_FILE"

#enable when vault is enabled
# shellcheck disable=SC1091
. "scripts/vault_auth.sh"

{

CFN_SUMO_ENDPOINT=$(vault kv get -field=sumo.collection.endpoint "kv2/prj/${VAULT_ENVIRONMENT}/${PROJECT_ID}/default")
export CFN_SUMO_ENDPOINT

# SLACK_WEBHOOK=$(vault kv get -field=slack.incoming.webhook "kv2/prj/${VAULT_ENVIRONMENT}/${PROJECT_ID}/default")
# CFN_SLACK_WEBHOOK=$(aws kms encrypt  --key-id "$CFN_KMS_KEY" \
#                                     --plaintext fileb://<(echo -n "$SLACK_WEBHOOK") \
#                                     --output text  \
#                                     --query CiphertextBlob \
#                                     --region "$AWS_DEFAULT_REGION" \
#                                     --encryption-context env="$CFN_CONTEXT")
#                                     #--plaintext "$SLACK_WEBHOOK" \ #enable when CLI v2 is installed
#                                     # --cli-binary-format raw-in-base64-out \ #enable when CLI v2 is installed
                                    
# export CFN_SLACK_WEBHOOK

} &> /dev/null


cfn_manage deploy-stack \
  --stack-name "$CFN_SUMO_SHIP" \
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/sumo-ship.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME"

cfn_manage deploy-stack \
    --stack-name "$CFN_LAMBDA_STACK" \
    --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/edge_lambda.yml" \
    --parameters-file "$PARAMS_FILE" \
    --role-name "$NONPRIV_ROLE_NAME"

cfn_manage deploy-stack \
    --stack-name "$CFN_WAF_STACK" \
    --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/edge_waf_cf_v2.yml" \
    --parameters-file "$PARAMS_FILE" \
    --role-name "$NONPRIV_ROLE_NAME"

cfn_manage deploy-stack \
    --stack-name "$CFN_FIREHOSE_STACK" \
    --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/edge_waf_firehose.yml" \
    --parameters-file "$PARAMS_FILE" \
    --role-name "$NONPRIV_ROLE_NAME"    