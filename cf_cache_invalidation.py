import boto3
import time
import os

def handler(event, context):
  client = boto3.client('cloudfront')
  path = []
  for items in event["Records"]:
    if "/index.html" in items["s3"]["object"]["key"]:
      lst=items["s3"]["object"]["key"].split("/",1)
      path.append("/"+lst[0]+"*")
      path.append("/")
    elif items["s3"]["object"]["key"] == 'index.html':
      path.append("/index.html")        
      path.append("/")
    elif items["s3"]["object"]["key"] == '/*':
      path.append("/*")
    else:
        print("index.html is not updated")
  
  print(f"path: {path}")
  if path:
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    bucket_origin = bucket_name + '.s3.ap-southeast-2.amazonaws.com'
    cloudfront_distribution_id = None
    paginator = client.get_paginator('list_distributions')
    page_iterator = paginator.paginate()
    for page in page_iterator:
      for distribution in page['DistributionList']['Items']:
          for cf_origin in distribution['Origins']['Items']:                  
                  if bucket_origin == cf_origin['DomainName']:                    
                    cloudfront_distribution_id = distribution['Id']
                    print(f"Origin: {cf_origin['DomainName']} Distribution ID: {cloudfront_distribution_id}")    
    invalidation = client.create_invalidation(DistributionId=cloudfront_distribution_id,
        InvalidationBatch={
            'Paths': {
                'Quantity': len(path),
                'Items': path
        },
        'CallerReference': str(time.time())
    })    
  else:
    print(f"Invalidation path list empty")
  # invalidation = client.create_invalidation(DistributionId='E2RU3S1JV7NDV3',
  #               InvalidationBatch={
  #                   'Paths': {
  #                       'Quantity': 1,
  #                       'Items': ['/*']
  #               },
  #               'CallerReference': str(time.time())
  #               })