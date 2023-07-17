'''
delete ecr repo
'''
import sys
import boto3
import time

def assumed_role_session(role_arn: str):
    '''
    change role
    '''
    role = boto3.client('sts').assume_role(RoleArn=role_arn, RoleSessionName='switch-role')
    credentials = role['Credentials']
    aws_access_key_id = credentials['AccessKeyId']
    aws_secret_access_key = credentials['SecretAccessKey']
    aws_session_token = credentials['SessionToken']
    return boto3.session.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token)
    
def get_aws_account(aws_env):
    '''
    determine environment
    '''
    if aws_env == 'dev' :
        acc='187628286232'
    elif aws_env == 'nonprod':
        acc='318263296841'
    elif aws_env == 'prod':
        acc='563000599290'
    elif aws_env == 'artefact':
        acc='847029211010'        
    else:
        print(f"cannot determine account for {aws_env}") 
        sys.exit(1)
    return acc


if __name__ == '__main__':
    aws_environment='artefact'
    project='vendorportal'
    ACCOUNT_ID=get_aws_account(aws_environment)
    assumed_session= assumed_role_session('arn:aws:iam::'+ACCOUNT_ID+':role/infra-cfnrole-'+project+'-nonprivileged')
    ECR = assumed_session.client('ecr', region_name='ap-southeast-2')

    response = ECR.delete_repository(    
      registryId='847029211010',
      repositoryName='vendorportal/stock-in-hand',
      force=True
)
    

