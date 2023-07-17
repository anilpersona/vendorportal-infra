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

def ssm_put_param(param_name,param_value):
  '''
  crete/update ssm param
  '''
  try:
    apse2_SSM.put_parameter(
      Name=param_name,
      Description='lambda-arn:version',
      Value=param_value,
      Type='String',    
      Overwrite=True,           
      Tier='Standard',    
      DataType='text'
    )
    print_msg("Updated SSM param with latest lambda Arn:Version",{param_name:param_value})

  except botocore.exceptions.ClientError as e:
    print(e)
    sys.exit(1)

def get_latest_lambda_version(fn_name):
	'''
  returns latest version arn
	'''
	marker = None
	response_iterator = paginator.paginate(
    FunctionName=fn_name,
    PaginationConfig={
        'MaxItems': 100,
        'PageSize': 15,
        'StartingToken': marker
    }
	)
	max_list=[]
	arn=''
	for page in response_iterator:		
		for i in range(len(page['Versions'])):
			try:			
				item=page['Versions'][i]
				big=int(item['Version'])
				arn=item['FunctionArn']
				max_list.append(big)
			except Exception:
				pass
	arn_string=arn.rsplit(':',1)[0]	
	return arn_string+":"+str(max(max_list))

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

def deploy_new_version(lambda_name,flag):
  '''
  conditionally deploy new lambda version
  '''
  output=""
  ssm_name="/vendorportal/arn/"+lambda_name
  if flag == "1":
    output=publish_new_version(lambda_name)
    ssm_put_param(ssm_name,output['arn'])

  else:
    print_msg("Deployment not needed",{"Lambda":lambda_name})
  create_ssm_ifnot_exits(ssm_name,lambda_name)

  return output

def create_ssm_ifnot_exits(ssm_name,fn_name):
  '''
  creates ssm if it does not exits
  '''
  try:
      apse2_SSM.get_parameter(Name=ssm_name)
  except botocore.exceptions.ClientError as e:
      print(e)
      try:
        ssm_value=get_latest_lambda_version(fn_name)
        ssm_put_param(ssm_name,ssm_value)
      except Exception as e:
        print_msg(e)
        sys.exit(1)
  except botocore.exceptions.ClientError as e:
    print_msg(e)
    sys.exit(1)

def publish_new_version(fn_name):
  '''
  publish a new version of lambda
  '''
  try:
    response=LAMBDA.publish_version(FunctionName=fn_name)
    _output={
      "arn":response['FunctionArn'],
      "version":response['Version']
    }
    print_msg("Deployed new version Lambda",_output)
    return _output
  except botocore.exceptions.ClientError as e:
    print(e)
    sys.exit(1)


if __name__ == '__main__':   

    user_data=str_to_dict(sys.argv[1])
    environment=user_data['aws_env']
    region=user_data['region']
    fn_name=user_data['lambda_name']
    publish_flag=user_data['publish']
    

    
    
    ACCOUNT_ID=get_aws_account(environment.lower())
    assumed_session= assumed_role_session('arn:aws:iam::'+ACCOUNT_ID+':role/infra-cfnrole-vendorportal-nonprivileged')
    LAMBDA = assumed_session.client('lambda', region_name=region)
    paginator = LAMBDA.get_paginator('list_versions_by_function')
    SSM = assumed_session.client('ssm', region_name=region)
    apse2_SSM = assumed_session.client('ssm', region_name="ap-southeast-2")

    

    utc_time = datetime.datetime.utcnow()
    local_time = datetime.datetime.now()
    print_time(utc_time,local_time)

    deploy_new_version(fn_name,publish_flag)
