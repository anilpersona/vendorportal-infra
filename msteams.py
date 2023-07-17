import urllib3
import json
import boto3
import os
import sys

client = boto3.client('ssm')
project="vendorportal"

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
    else:
        print(f"cannot determine account for {aws_env}") 
        sys.exit(1)
    return acc

def assumed_role_session(role_arn: str):
    '''
    change role
    '''
    try:
      role = boto3.client('sts').assume_role(RoleArn=role_arn, RoleSessionName='switch-role')
      credentials = role['Credentials']
      aws_access_key_id = credentials['AccessKeyId']
      aws_secret_access_key = credentials['SecretAccessKey']
      aws_session_token = credentials['SessionToken']
      return boto3.session.Session(
          aws_access_key_id=aws_access_key_id,
          aws_secret_access_key=aws_secret_access_key,
          aws_session_token=aws_session_token)
    except Exception as e:
      print(f"Exception: {e} , using local keys")
      return boto3.session.Session(
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        aws_session_token=os.environ["AWS_SESSION_TOKEN"]
      )    
      
def get_parameter (client):
    
    Parameter = client.get_parameter(
        Name='/vendorportal/osb/webhook/msteams',
        WithDecryption=True
        )
    print(Parameter)
    return Parameter ['Parameter']['Value']


class TeamsWebhookException(Exception):
    """custom exception for failed webhook call"""
    pass


class ConnectorCard:
    def __init__(self, hookurl, http_timeout=60):
        self.http = urllib3.PoolManager()
        self.payload = {}
        self.hookurl = hookurl
        self.http_timeout = http_timeout

    def text(self, mtext):
        self.payload["text"] = mtext
        return self

    def send(self):
        headers = {"Content-Type":"application/json"}
        r = self.http.request(
                'POST',
                f'{self.hookurl}',
                body=json.dumps(self.payload).encode('utf-8'),
                headers=headers, timeout=self.http_timeout)
        
        if r.status != 200:
            raise ValueError(
                'Request to MS Teams returned an error %s'
                 % (r.status)
            )
        

if __name__ == "__main__":
    
    # ACCOUNT_ID=get_aws_account(' dev')
    # assumed_session= assumed_role_session('arn:aws:iam::'+ACCOUNT_ID+':role/infra-cfnrole-vendorportal-nonprivileged')
    
    MSTEAMS_WEBHOOK = get_parameter(client)
    myTeamsMessage = ConnectorCard(MSTEAMS_WEBHOOK)
    myTeamsMessage.text("this is testing 222")
    myTeamsMessage.send()
    print(myTeamsMessage.text)