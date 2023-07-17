#!/bin/bash

# exit when any command fails
set +e

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


LAMBDA=$(aws ssm get-parameters-by-path\
                          --path "/${PROJECT_ID}/lambda/iam-role-arn/" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameters[].{Name: Name, Value: Value}")
                          #--output text || echo -n "")
# shellcheck disable=SC2183,SC2046,SC2086,SC2006,SC2027
LAMBDA_EXPORTS=`echo $LAMBDA | jq ' .  | from_entries
                         | with_entries(.key |=split("/")[-1])
                         | with_entries(.key |= ascii_upcase)
                         | with_entries(.key |="CFN_ROLE_LAMBDA_" + .)
                         | with_entries(.key |= gsub("-";"_"))'`

set +e
# shellcheck disable=SC2183,SC2046,SC2086,SC2006,SC2027
IFS=$',' read -r -s -d ''  -a CFN_LAMBDA_EXPORTS <<< """$LAMBDA_EXPORTS"""

for item in "${CFN_LAMBDA_EXPORTS[@]}"
do
        key=$(echo "$item" | cut -d ":" -f1 | tr -d " " | tr -d "}" | tr -d "{" | tr -d ":" | tr -d '"' | xargs)
        value=$(echo "$item" |  cut -d ":" -f 2-  | tr -d " " | tr -d "}" | tr -d "{" | tr -d '"' | xargs)
        # shellcheck disable=SC2183,SC2046,SC2086,SC2006,SC2027
        export $key="$value"

done
set -e
ECS=$(aws ssm get-parameters-by-path\
                          --path "/${PROJECT_ID}/ecs/iam-role-arn/" \
                          --region "${AWS_DEFAULT_REGION}" \
                          --no-with-decryption \
                          --query "Parameters[].{Name: Name, Value: Value}")
                          #--output text || echo -n "")
# shellcheck disable=SC2183,SC2046,SC2086,SC2006,SC2027
ECS_EXPORTS=`echo $ECS | jq ' .  | from_entries
                         | with_entries(.key |=split("/")[-1])
                         | with_entries(.key |= ascii_upcase)
                         | with_entries(.key |="CFN_ROLE_ECS_" + .)
                         | with_entries(.key |= gsub("-";"_"))'`
set +e
# shellcheck disable=SC2183,SC2046,SC2086,SC2006,SC2027
IFS=$',' read -r -s -d  '' -a CFN_ECS_EXPORTS <<< """$ECS_EXPORTS"""

for item in "${CFN_ECS_EXPORTS[@]}"
do
        key=$(echo "$item" | cut -d ":" -f1 | tr -d " " | tr -d "}" | tr -d "{" | tr -d ":" | tr -d '"' | xargs)
        value=$(echo "$item" |  cut -d ":" -f 2- | tr -d " " | tr -d "}" | tr -d "{" | tr -d '"' | xargs)
        # shellcheck disable=SC2183,SC2046,SC2086,SC2006,SC2027
        export $key="$value"
done

env | grep CFN_ROLE_
set -e

#enable old values
export AWS_ACCESS_KEY_ID=$OLD_AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY=$OLD_AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN