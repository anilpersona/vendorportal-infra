# vendorportal-create-secret
Creates secrets using  kms encrypted ssm and security manager(in dev)

## Capabilities

* List all the secrets keys of a environment
* Create a enrypted ssm paramter

## Inputs

### Type of action
* choice - Type of environment (dev/nonprod/prod)
* checkbox - List all secrets (true/false)
* checkbox - create a secret (true/false)

### Secret Details
* choice - Type of secret store (ssm - AWS SSM / sm - AWS Secret Manager)
* string - Enter a parameter name or path (eg /vendorportal/client/id) , initial "/" is mandatory
* string - Value , max length 4096
