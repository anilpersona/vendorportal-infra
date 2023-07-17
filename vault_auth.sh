#!/bin/bash

# http://blog.kablamo.org/2015/11/08/bash-tricks-eux/
set -euo pipefail

export VAULT_ADDR="https://vault.kaccess.net:8200"

export HEADER_VALUE="vault.kaccess.net"

{
if [[ -z "${VAULT_TOKEN-}" ]]
then
    # echo "Authenticate to vault"
    VAULT_TOKEN=$(vault login -token-only -method=aws header_value="${HEADER_VALUE}" "role=jenkins-${PROJECT_ID}-${VAULT_ENVIRONMENT}")
    export VAULT_TOKEN
fi
} &> /dev/null
