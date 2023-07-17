#!/bin/bash

# http://blog.kablamo.org/2015/11/08/bash-tricks-eux/
set -euxo pipefail
cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
. "scripts/stack_name_vars.sh"

NONPRIV_ROLE_NAME='infra-cfnrole-vendorportal-nonprivileged'

# delete ecr repo
#python3 scripts/python/delete_ecr_repo.py

cfn_manage deploy-stack \
    --stack-name "$CFN_ECR_STACK" \
    --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/ecr.yml" \
    --parameters-file "cloudformation/params/${CFN_ENVIRONMENT}.yml" \
    --role-name "$NONPRIV_ROLE_NAME"
