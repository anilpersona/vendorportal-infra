#!/bin/bash

# http://blog.kablamo.org/2015/11/08/bash-tricks-eux/
set -euxo pipefail
cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
. "scripts/stack_name_vars.sh"

NONPRIV_ROLE_NAME='infra-cfnrole-vendorportal-nonprivileged'

export CFN_FACADE_TASK_STACK="vendorportal-stack-ecs-task-${CFN_ENVIRONMENT}"
export CFN_MATERIAL_LIB_TASK_STACK="vendorportal-stack-material-library-${CFN_ENVIRONMENT}"


cfn_manage delete-stack \
  --stack-name "vendorportal-stack-rds-nonprod"\
  --role-name "$NONPRIV_ROLE_NAME"
