from asyncio.log import logger
import boto3
import json
import logging
import sys
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(funcName)s:%(message)s')
client=boto3.client("sts",region_name="ap-southeast-2")
response = client.get_caller_identity()
print(response["Account"])