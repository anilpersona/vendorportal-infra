#!/bin/bash

# http://blog.kablamo.org/2015/11/08/bash-tricks-eux/
# set -uxo pipefail
# cd "$(dirname "$0")/.." || exit 1

# rc=0
# while read -r -u10 file; do
#   aws cloudformation validate-template --template-body "file://$(pwd)/${file}" >/dev/null || rc=$?
# done 10< <(find ./cloudformation/templates -type f -iname '*.yml' -o -iname '*.yaml' -o -iname '*.json' -o -iname '*.template' -o -iname '*.cf')

# exit $rc

set -uxo pipefail
cd "$(dirname "$0")/.." || exit 1

rc=0

for entry in "$CFN_TEMPLATE_DIR"/*
do
	filename=$(basename "${entry}")
  	aws cloudformation validate-template --template-url "https://${CFN_ARTIFACT_BUCKET}.s3.amazonaws.com/infra/cloudformation/${CFN_BRANCH_NAME}-${CFN_BUILD_NUMBER}/templates/${filename}" >/dev/null || rc=$?
done
exit $rc