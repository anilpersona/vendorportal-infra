import boto3
import sys
import os
import botocore

# check if ssm param exits
 
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

def ssm_put_param(param_name,param_value,SSM):
  '''
  crete/update ssm param
  '''
  try:
    SSM.put_parameter(
      Name=param_name,
      Description='latest file name admin tool',
      Value=param_value,
      Type='String',    
      Overwrite=True,           
      Tier='Standard',    
      DataType='text'
    )
    print_msg("Updated SSM param with latest file name",{param_name:param_value})

  except botocore.exceptions.ClientError as e:
    print(e)
    sys.exit(1)

    
def handler(event, context):
  print(event)
  SSM = boto3.client('ssm')
  AWS_ENV=os.environ['AWS_ENV']
  WIN_PARAM=os.environ['WIN_LATEST_ADMIN_TOOL_SSM']
  MAC_PARAM=os.environ['MAC_LATEST_ADMIN_TOOL_SSM']

  for items in event["Records"]:
    s3_file_path=items["s3"]["object"]["key"]
    param_val=s3_file_path
    if 'windows/' in s3_file_path:
      ssm_put_param(WIN_PARAM,param_val,SSM)
    elif 'mac/' in s3_file_path:
      ssm_put_param(MAC_PARAM,param_val,SSM)
    else:
      print("no match")
