import json
import boto3
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

assumed_session= assumed_role_session('arn:aws:iam::'+'187628286232'+':role/infra-cfnrole-vendorportal-nonprivileged')
S3 = assumed_session.client('s3', region_name="ap-southeast-2")        
# Create a bucket policy
bucket_name = 'kmartau-vendorportal-logs-dev'
S3.delete_bucket_policy(Bucket=bucket_name)