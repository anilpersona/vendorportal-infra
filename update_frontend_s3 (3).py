'''
Usage:
This program delete files from frontend bucket
params:
  1. aws_environment: allowed values are dev|nonprod|prod , required
  2. prefix: eg. "landing-page/" , required
'''
import sys
import boto3
import time
import botocore


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
    except botocore.exceptions.ClientError as e:
      if e.response['Error']['Code'] == 'InvalidClientTokenId':
        print_msg("Please use new tokens",{"error":e.response['Error']['Message']})
      elif e.response['Error']['Code'] == 'AccessDenied':
        print_msg("Insufficient permission",{"error":e.response['Error']['Message']})        
      else:
        print(e)
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
def get_cf_distribution(aws_env):
    '''
    determine cf id
    '''
    if aws_env == 'dev' :
        cf_dist='E2RU3S1JV7NDV3'
    elif aws_env == 'nonprod':
        cf_dist='E4LB4M0UKEQAM'
    elif aws_env == 'prod':
        cf_dist='EGAZ643F5HJAE'       
    else:
        print(f"cannot determine cf distribution id for {aws_env}") 
        sys.exit(1)
    return cf_dist
def put_item(client,bucket_name,prefix):
  file_name='s3_pref_list.txt'
  response = client.put_object(
    
    Body=file_name,
    Bucket=bucket_name,    
    Key=prefix+file_name,    
    ServerSideEncryption='AES256',    
  )

def list_object_versions(client,bucket_name,pref):
  '''
  List object versions from s3
  params: s3 client , bucket name , prefix
  returns: list of dictionaries , object key and object versions
  '''
  obj_list=[]
  flag=1
  marker = None
  while flag:
    paginator = client.get_paginator('list_object_versions')
    response_iterator = paginator.paginate(
      Bucket=bucket_name,
      Prefix=pref,
      PaginationConfig={
          'MaxItems': 2000,
          'PageSize': 480,
          'StartingToken': marker
      }
    )
    try:
      for page in response_iterator:
        for i in range(len(page['Versions'])):
          obj_list.append({"Key":page["Versions"][i]["Key"],"VersionId":page["Versions"][i]["VersionId"]})
        # print(f"Items in first list iteration {len(obj_list)}")
        try:
            marker = page['NextKeyMarker']        
        except KeyError:
            flag=0
            break
    except Exception as e:
      # print(e.args)
      if e.args[0] == "Versions":
        print_msg("No items avaible",{"Prefix":pref})
        flag=0
        break
      else:
        print_msg(e)
        sys.exit(1)
  return obj_list

def delete_from_s3(client,frontend_bucket,prefix,artifact_bucket):
  '''
  delete items for a particular prefix
  '''
  try:
    count=0  
    obj_list=list_object_versions(client,frontend_bucket,prefix)
    print_msg("Object list obtained",{"count":len(obj_list)})
    file = open("s3_pref_list.txt", "w")
    for i in obj_list:
      count=count+1
      file.write(f"{count}: {i} \n")
    file.close()
    put_item(client,artifact_bucket,"frontend-bucket-activity-logs/")
    for i in range(0,len(obj_list),950):
      list_to_delete=obj_list[i:i+950]
      print_msg("Deleting items",{"count":len(list_to_delete)})
      response = client.delete_objects(
          Bucket=frontend_bucket,
          Delete={
              'Objects':list_to_delete,
              'Quiet': False
          }   
      )
    return 1
  except Exception as e:
    print(e)
    return 0

def remove_cf_cache(client,cf_id,prefix):
  try:
    print_msg("Invalidate Cloudfront cache",{"path":prefix})
    prefix_path=prefix.split('/')[0]
    path=['/', '/'+prefix_path+'*']
    invalidation = client.create_invalidation(DistributionId=cf_id,
                  InvalidationBatch={
                      'Paths': {
                          'Quantity': 2,
                          'Items': path
                  },
                  'CallerReference': str(time.time())
                  })
  except Exception as e:
    print_msg("Unable to invalidate cache")
    print(e)
if __name__ == '__main__':
  if len(sys.argv) == 3:
    aws_environment=sys.argv[1]    
    s3prefix=sys.argv[2]
    project='vendorportal'
    ACCOUNT_ID=get_aws_account(aws_environment)
    CF_DIST_ID=get_cf_distribution(aws_environment)
    assumed_session= assumed_role_session('arn:aws:iam::'+ACCOUNT_ID+':role/infra-cfnrole-'+project+'-nonprivileged')
    if assumed_session:
      print_msg("Trying Assumed Creds")
      s3 = assumed_session.client('s3', region_name="ap-southeast-2")
      cf = assumed_session.client('cloudfront', region_name="ap-southeast-2")
    else:
      print_msg("Trying Local Creds")
      s3 = boto3.client('s3')
      cf = boto3.client('cloudfront')    
    artifact_bucket_name='kmartau-vendorportal-artifact-'+aws_environment
    frontend_bucket_name='kmartau-vendorportal-frontend-'+aws_environment
    delete_from_s3(s3,frontend_bucket_name,s3prefix,artifact_bucket_name)
    remove_cf_cache(cf,CF_DIST_ID,s3prefix)
    print_msg("End")
  else:
    print_msg("Not Enough arguments")
    print(__doc__)
