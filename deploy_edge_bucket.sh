#!/bin/bash

# http://blog.kablamo.org/2015/11/08/bash-tricks-eux/
set -euxo pipefail
cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
. "scripts/stack_name_vars.sh"

NONPRIV_ROLE_NAME='infra-cfnrole-vendorportal-nonprivileged'
PARAMS_FILE="cloudformation/params/${CFN_ENVIRONMENT}/${AWS_DEFAULT_REGION}.yml"

cfn_manage deploy-stack \
  --stack-name "$CFN_EDGE_S3_STACK" \
  --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/edge_s3.yml" \
  --parameters-file "$PARAMS_FILE" \
  --role-name "$NONPRIV_ROLE_NAME"