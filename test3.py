from asyncio.log import logger
import boto3
import json
import logging
import sys
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(funcName)s:%(message)s')

project="vendorportal"
def is_existing_kms(client,alias=None):
  '''
  kms
  '''
  try:
    if client.describe_key(KeyId=alias): return True
  except Exception as e:
    logging.exception(f"{e.response['Error']['Message']}---------------")
def set_kms_alias(client,key_alias=None):
  if not key_alias:    
    logging.info(f"checking custom kms key : alias/{project}/secret")
    if is_existing_kms(client,f"alias/{project}/secret1"):
      logging.info(f"found: custom kms key for secrets , alias: alias/{project}/secret")
      return f"alias/{project}/secret"
    else:
      logging.info("not found: custom key , using default service keys")        
      return "alias/aws/ssm","alias/aws/secretmanager"      
  else:
    logging.info("checking passed alias,")
    if is_existing_kms(client,key_alias):
      logging.info(f"using passed alias {key_alias}")
      return key_alias

if __name__ == "__main__":
  kms=boto3.client("kms",region_name="ap-southeast-2")
  val=set_kms_alias(kms,"alias/vendorportal/general")
  print(type(val))
  print(len(val))