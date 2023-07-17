from cmath import log
import sys
import boto3
import json
import os
import datetime
import botocore
from botocore.config import Config
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(funcName)s:%(message)s')

def get_env_vars():
  
  mandatory=["AWS_REGION","AWS_DEV_ACC","AWS_NONPROD_ACC","AWS_PROD_ACC","PROJECT"]  
  for var in mandatory:    
    try:
      os.environ[var]
    except KeyError as e:
      logging.error(f"{var} is not set")
      sys.exit(1)

def set_env_vars():
  try:
      proxy=os.environ['HTTP_PROXY']
      proxy_uri=proxy.split('//')[1]
  except Exception as e:
    logging.warning("Proxy is not set using no proxy")
    proxy_uri=None
    proxy=None  
  region=os.environ["AWS_REGION"]
  project=os.environ["PROJECT"]
  return region,proxy_uri,proxy,project

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

def is_existing_kms(client,alias=None):
  '''
  kms
  '''
  try:
    if client.describe_key(KeyId=alias): return True
  except Exception as e:
    logging.exception(e)

def set_kms_alias(client,key_alias=None):
  if not key_alias:    
    logging.info(f"checking custom kms key : alias/{project}/secret")
    if is_existing_kms(client,f"alias/{project}/secret"):
      logging.info(f"found: custom kms key for secrets , alias: alias/{project}/secret")
      return f"alias/{project}/secret",f"alias/{project}/secret"
    else:
      logging.info("not found: custom key , using default service keys")        
      return "alias/aws/ssm","alias/aws/secretmanager"      
  else:
    logging.info("checking passed alias,")
    if is_existing_kms(client,key_alias):
      logging.info(f"using passed alias {key_alias}")
      return key_alias,key_alias
    
def get_aws_account(aws_env):
    '''
    determine environment
    '''
    if aws_env == 'dev' :
        acc=os.environ["AWS_DEV_ACC"]
    elif aws_env == 'nonprod':
        acc=os.environ["AWS_NONPROD_ACC"]
    elif aws_env == 'prod':
        acc=os.environ["AWS_PROD_ACC"]
    else:
        logging.warning(f"cannot determine account for {aws_env}") 
        sys.exit(1)
    return acc

def print_json(msg):
  print(json.dumps(msg,indent=4,sort_keys=True,default=str))

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

def get_timestamp_str():
    '''
    get string format current time in UTC 
    '''
    _ct = datetime.datetime.utcnow()
    _time_stamp_str = _ct.strftime("%d-%b-%Y-%H-%M-%S") 
    return _time_stamp_str

def get_ssm(SSM,ssm_name):  
  '''
  Get DocumentDB host and port value from AWS SSM
  Exit if Get fails

  Arg:
      SSM Client
      SSM Param Name
  Raises:
      ClientError: If there is some error while calling ssm api

  '''
  try:
    resp=SSM.get_parameter(Name=ssm_name,WithDecryption=False)
    return resp['Parameter']['Value']
  except botocore.exceptions.ClientError as e:
    print(f"ssm fetch error:{e}")
    sys.exit(1)

def parse_payload(payload):
  '''
  convert a regular or json string to dictionary
  '''
  logging.debug(f"raw payload {type(payload)}--{payload}")
  lst=payload.strip("[]").split(":",1)
  _user_data_dict={}
  _user_data_dict[lst[0]]=lst[1]
  return _user_data_dict

def create_enc_ssm(client,param_name,param_value):
  '''
  create/update ssm param
  '''
  try:
    client.put_parameter(
      Name=param_name,
      Description=f"{project}-secret",
      Value=param_value,
      Type='SecureString',
      Overwrite=True,           
      Tier='Standard',
      KeyId=KMS_SSM 
    )
    print_msg("secret created",{"Name":param_name})

  except botocore.exceptions.ClientError as e:
    print(e)
    sys.exit(1)

def ssm_describe_secrets(client):
  '''
  Get all project secrets from AWS SSM

  Arg:
      SSM Client
  Raises:
      Exception: If there is some error while calling ssm api

  '''
  paginator=client.get_paginator('describe_parameters')
  flag=1
  secret_list=[]
  marker=None
  while flag:
    try:
      response_iterator = paginator.paginate(
        ParameterFilters=[
            {
                'Key': 'KeyId',
                'Values': [KMS_SM,"alias/aws/ssm"]
            },
            {
                'Key': 'Path',
                'Option': 'Recursive',
                'Values': ['/'+project]
            },
        ],
        PaginationConfig={
            'MaxItems': 10,
            'PageSize': 10,
            'StartingToken': marker
        }
      )
    except Exception as e:
      logging.exception(e)
      sys.exit(1)
    for page in response_iterator:
      for i in range(len(page['Parameters'])):
          secret_list.append(page['Parameters'][i]['Name'])
      try:
          marker = page['NextToken']        
      except KeyError:
        flag=0
        break

  return secret_list

def secman_describe_secrets(client):
  '''
  Get all project secrets from AWS SecretManager

  Arg:
      SM Client
  Raises:
      Exception: If there is some error while calling sm api

  '''
  paginator=client.get_paginator('list_secrets')
  flag=1
  secret_list=[]
  marker=None
  while flag:
    try:
      response_iterator = paginator.paginate(
        Filters=[
          {
              'Key': 'tag-key',
              'Values': [ 'Project']
          },
          {
              'Key': 'tag-value',
              'Values': [ project ]
          }
        ],
        SortOrder='asc',
        PaginationConfig={
            'MaxItems': 2,
            'PageSize': 2,
            'StartingToken': marker
        }
      )
    except Exception as e:
      logging.exception(e)
    for page in response_iterator:
      for i in range(len(page['SecretList'])):
          secret_list.append(page['SecretList'][i]['Name'])
      try:
          marker = page['NextToken']        
      except KeyError:
        flag=0
        break

  return secret_list

def get_db_info(client,db_identifier=None):
  '''
  Get AWS DocumentDb/RDS info

  Arg:
      docdb/rds Client
      db unique identifier
  Returns:
      dict: db object in secret manager format      
  Raises:
      TypeError: If db indetifier not found
      Exception: If error while describing db cluster
  '''  
  if not db_identifier:
    raise TypeError("db idetifier is empty, exiting")    
  else:
    try:
      response = client.describe_db_clusters(DBClusterIdentifier=db_identifier)
      db_cluster=response["DBClusters"][0]     
      _db_info={
        "engine": "mongo" if db_cluster["Engine"] == "docdb" else db_cluster["Engine"] ,
        "host": db_cluster["Endpoint"],
        "port": db_cluster["Port"],
        "ssl": "true",
        "dbClusterIdentifier": db_cluster["DBClusterIdentifier"] 
      }
      return _db_info
    except Exception as e:
      logging.exception(e)
      print_msg("Given DB not found, Please check db identifier")
      sys.exit(1)

def get_secret_string(secret_payload,db_identifier=None):
  '''
  Form final DocumentDb/RDS secret object

  Arg:
      docdb/rds secret payload
      db unique identifier
  Returns:
      final DocumentDb/RDS secret object      
  Raises:
      TypeError: If db indetifier not found
      Exception: dict error
  '''    
  if not db_identifier:
    raise TypeError("db idetifier is empty, exiting")    
  else:
    try:
      if(db_identifier):
        _secret_json_dict=get_db_info(docdb, db_identifier)
        _secret_json_dict['username']=secret_payload["username"]
        _secret_json_dict['password']=secret_payload["password"]
        return _secret_json_dict
    except Exception as e:
      logging.exception(e)
      sys.exit(1)

def is_new_secret(client,path):
  '''
  Check if a secert manager secret exists

  Arg:
      sm client
      sm secret path
  Returns:
      None: if no secret found or multiple secret found
      Dict: arn and name of secret
  Raises:      
      Exception: error while listing secret
  '''      
  try:    
    response = client.list_secrets(Filters=[{'Key': 'name','Values': [path]}])
    if not len(response["SecretList"]):
      logging.info("secret does not exist")
      return None
    elif len(response["SecretList"]) == 1:
      logging.info("secret exists")
      return { "arn":response["SecretList"][0]["ARN"] , "name": response["SecretList"][0]["Name"]}
    else:
      logging.error("mulitple secret found,exiting")
      sys.exit(1)

  except Exception as e:
    logging.exception("listing secrets issue")

def create_secret_manger_secrets(client,param):
  '''
  Create a secert manager secret

  Arg:
      sm client
      sm secret metadata
      sm secret path
      sm secret object in sm secret format for db     
      db unique identfier
  Returns:
      None: if no secret found or multiple secret found
      Dict: arn and name of secret
  Raises:      
      Exception: error while updating secret
  ''' 
  try:
    secret_json_string=get_secret_string(param["secret_payload"],param["db_identifier"])
    if secret_json_string: 
      if param["secret_metadata"]:
        print_msg("Updating secret")
        try:
          response = client.update_secret(
              SecretId=param["secret_metadata"]["arn"],
              SecretString=json.dumps(secret_json_string)
          )
          print_msg("Secret Updated",{"Name":response['Name']})
        except Exception as e:
          logging.exception(f"exception: updating secret {e}")

      else:
        print_msg("Creating a secret")
        try:
          response = client.create_secret(
            Name=param["secret_path"],
            Description=param["description"],
            KmsKeyId=KMS_SM,
            SecretString=json.dumps(secret_json_string),
            Tags=[
                  {'Key': 'Project','Value': project},
                  {'Key': 'Billing','Value': project},
                  {'Key': 'Owner','Value': project}
            ]
          )
          print_msg("Secret Created",{"Name":response['Name']})
      
        except Exception as e:        
          logging.exception(f"create_secret--{e}--")
    logging.info("enabling secret rotation")        
    rotate_secret(sm,response["ARN"])    
  except Exception as e:
    logging.exception(f"{e}")

def rotate_secret(client,secret_arn):
  '''
  Enables secert rotations for secret manager secrets

  Arg:
      sm client
      sm secret arn      
  Returns:
      None
  Raises:      
      Exception: error while enabling rotation
  '''
  try:
    lambda_ssm=f"/{project}/lambda/arn/secrotv2"
    rotation_lambda_arn=get_ssm(ssm,lambda_ssm)
    response = client.rotate_secret(
        SecretId=secret_arn,
        RotationLambdaARN=rotation_lambda_arn,
        RotationRules={
            'Duration': '1h',
            'ScheduleExpression': 'cron(0 13 1 * ? *)'
        },
        RotateImmediately=True
    )
    logging.info("Secret rotation enabled")
  except Exception as e:
    logging.exception(f"error while enabling secret rotation{e}")

  

if __name__ == "__main__":

  logging.info(f"***Initialize***")
  get_env_vars()
  region,proxy_uri,proxy,project=set_env_vars()

  if len(sys.argv) >= 3:
    
    regular_payload=str_to_dict(sys.argv[1])
    ACCOUNT_ID=get_aws_account(regular_payload['AWS_ENVIRONMENT'].lower())
    logging.info(f"Account: {ACCOUNT_ID}")
    assumed_session= assumed_role_session(f"arn:aws:iam::{ACCOUNT_ID}:role/infra-cfnrole-{project}-nonprivileged")

    configg=Config(
      connect_timeout=10,
      read_timeout=200,
      region_name=region,
      retries={'max_attempts': 2},
      proxies={'https': proxy_uri,'http': proxy_uri},
    ) 

    client_conf={
        "SSM":assumed_session.client('ssm', config=configg),
        "SM":assumed_session.client('secretsmanager', config=configg),
        "DOCDB":assumed_session.client('docdb', config=configg),
        "RDS":assumed_session.client('rds', config=configg),
        "KMS":assumed_session.client('kms', config=configg)
    }

    sm = client_conf["SM"]
    ssm = client_conf["SSM"]
    docdb= client_conf["DOCDB"]
    rds= client_conf["RDS"]
    kms= client_conf["KMS"]

    list_secret=regular_payload['LIST_ALL_SECRETS']
    docdb_secret=regular_payload['DOCDB_SECRET']
    rds_secret=regular_payload['RDS_SECRET']
    other_secret=regular_payload['OTHER_SECRET']

    KMS_SSM,KMS_SM=set_kms_alias(kms)
    logging.info(f"kms key for ssm {KMS_SSM} |  kms key for sm {KMS_SM}")
    
    if(list_secret == "true"):
      ssm_list=ssm_describe_secrets(ssm)
      secman_list=secman_describe_secrets(sm)
      total_list=ssm_list+secman_list
      print_msg("List of secrets",{project:regular_payload['AWS_ENVIRONMENT'] })
      for i in range(len(total_list)):
        print(f"{i+1}: {total_list[i]}")
      print_msg("End of List")
    elif (other_secret == "true"):
      secret_payload=parse_payload(sys.argv[2])
      logging.debug(f"payload type: {type(secret_payload)}")
      # regular_payload['sec_param_val']=secret_payload['sec_param_val']            
      create_enc_ssm(ssm,regular_payload['sec_param_path'],secret_payload['sec_param_val'])
    elif (docdb_secret == "true"):         
      param={
        "secret_payload": json.loads(parse_payload(sys.argv[2])['sec_param_val']),
        "secret_path": regular_payload['sec_param_path'] ,     
        "db_identifier": regular_payload['sec_param_dbi'], #"vendorportaldbcluster-6pycmgfxywty"
        "description": regular_payload['sec_param_desc'],
        "secret_metadata": is_new_secret(sm,regular_payload['sec_param_path']) 
      }      
      create_secret_manger_secrets(sm,param)
    elif (rds_secret == "true"):
      print_msg("not supported yet")
      
    #   secret_payload=json.loads(parse_payload(sys.argv[2])['sec_param_val'])
    #   secret_path=regular_payload['sec_param_path']        
    #   dbi=regular_payload['sec_param_dbi'] #"vendorportaldbcluster-6pycmgfxywty"
    #   description=regular_payload['sec_param_desc']               
    #   secret_metadata=is_new_secret(sm,secret_path)
    #   create_secret_manger_secrets(sm,secret_metadata,secret_path,secret_payload,description,dbi)
    else:                
      logging.warning("no action")
  else:
    logging.error("not enough arguments")
    sys.exit(1)
  logging.info("End!")  


