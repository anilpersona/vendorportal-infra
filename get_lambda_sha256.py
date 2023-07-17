'''
get sha256 of lambda
get sha256 of local zip file
'''
import sys
import datetime
import os
import boto3
import botocore
import json
import hashlib
import base64

def list_to_dict(lst):
    '''
    convert a list to dictionary with 1,2,3 as key value
    Example    
    input : ["Monday","Tuesday","Wednesday"]
    output: {1:"Monday",2:"Tuesday",3:"Wednesday"}
    '''
    _dict= { i:lst[i-1] for i in range(1,len(lst)+1)}
    return _dict

def str_to_dict(user_data_str):
    '''
    return dictionary
    '''
    lst=user_data_str.strip('[]').split(',')
    _user_data_dict={}
    for item in lst:
        ele=item.split(':')
        _user_data_dict[ele[0].strip()]=ele[1].strip()
    return _user_data_dict

def str_to_datetime(user_data_date,user_data_time):
    '''
    return a datetime object
    '''
    _datetime_str=user_data_date+" "+user_data_time
    _datetime_obj= datetime.datetime.strptime(_datetime_str,'%d-%m-%Y %H-%M-%S')
    return _datetime_obj

def print_msg(msg,*args):
    '''
    print status
    '''    
    print(f"\n{80*'#'}\n\n{msg}!")
    if len(args) == 1 and {} in args:
        print("No Items")
    for item in args:
        for key,value in item.items():
            print(f"\n{key} : {value}")
    print(f"\n{80*'#'}\n")

def print_time(utc,local):
    '''
    print time
    '''
    utc_timestamp_str = utc.strftime("%d-%b-%Y-%H-%M-%S")
    local_timestamp_str = local.strftime("%d-%b-%Y-%H-%M-%S")
    print(f"Current time UTC: {utc_timestamp_str}")
    print(f"Current time local: {local_timestamp_str}")      


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
    else:
        print(f"cannot determine account for {aws_env}") 
        sys.exit(1)
    return acc


def get_lambda_info(lambda_name):
  '''
  return lambda function hash
  '''
  try:
    response = LAMBDA.get_function(
      FunctionName=lambda_name,
      Qualifier="$LATEST"
    )
    result=response['Configuration']['CodeSha256']
    return result
  except botocore.exceptions.ClientError as error:
    print(error)
    sys.exit(1)
    
def get_local_package_hash(local_package_name):
  '''
  get local package hash
  '''
  try:
    ldata = ''
    file_name=os.path.join(os.getcwd(),local_package_name)
    with open(file_name,'rb') as f:
        ldata = f.read()
        if ldata:
            m = hashlib.sha256()
            m.update(ldata)
            s3_digest = m.digest()
            local_codesha256 = base64.b64encode(s3_digest)
            print(f"{local_codesha256} --------")        
            return local_codesha256.decode('utf-8')
  except FileNotFoundError as e:
    print_msg(e)
    sys.exit(1)
  
def ssm_put_param(param_name,param_value):
  '''
  crete/update ssm param
  '''
  try:
    SSM.put_parameter(
      Name=param_name,
      Description='flag to deploy new lambda vesion',
      Value=str(param_value),
      Type='String',    
      Overwrite=True,
      AllowedPattern='^(0|1)$',      
      Tier='Standard',    
      DataType='text'
    )
    print_msg("updated Param ")
  except botocore.exceptions.ClientError as e:
    print(e)
    sys.exit(1)
  except botocore.exceptions.ParamValidationError as e:
    print(e)
    sys.exit(1)

if __name__ == '__main__':   

    user_data=str_to_dict(sys.argv[1])
    environment=user_data['aws_env']
    region=user_data['region']
    fn_name=user_data['lambda_name']
    local_file=user_data['local_deployment_package']
    ssm_name="/vendorportal/"+fn_name
    
    ACCOUNT_ID=get_aws_account(environment.lower())
    assumed_session= assumed_role_session('arn:aws:iam::'+ACCOUNT_ID+':role/infra-cfnrole-vendorportal-nonprivileged')
    LAMBDA = assumed_session.client('lambda', region_name=region)
    SSM = assumed_session.client('ssm', region_name=region)

    utc_time = datetime.datetime.utcnow()
    local_time = datetime.datetime.now()
    print_time(utc_time,local_time)

    remote_b64_sha256=get_lambda_info(fn_name)
    local_b64_sha256=get_local_package_hash(local_file)

    print(f"remote {remote_b64_sha256} {type(remote_b64_sha256)}")
    print(f"local {local_b64_sha256} {type(local_b64_sha256)}")

    if remote_b64_sha256 == local_b64_sha256:
      ssm_value=0
    else:
      ssm_value=1
    ssm_put_param(ssm_name,ssm_value)
