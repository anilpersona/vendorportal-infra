import json
import boto3

if __name__ =="__main__":

      sm=boto3.client("secretsmanager",region_name="ap-southeast-2")
      response = sm.create_secret(
          Name="/vendorportal/seceret/test4",
          Description="test",
          # KmsKeyId="fc2e872c-846e-480a-8ffe-bea7067ed8a7",
          KmsKeyId="alias/aws/secretsmanager",
          SecretString=json.dumps({
          "engine": "mongo",
          "host": "vendorportaldbcluster-6pycmgfxywty.cluster-cfwafydn4lat.ap-southeast-2.docdb.amazonaws.com",
          "port": 21010,
          "ssl": "True",
          "dbClusterIdentifier": "vendorportaldbcluster-6pycmgfxywty",
          "username": "one",
          "password": "two"
          }),
          Tags=[
                {'Key': 'Project','Value': "vendorportal"},
                {'Key': 'Billing','Value': "vendorportal"},
                {'Key': 'Owner','Value': "vendorportal"}
          ]
      )

      arn=response["ARN"]
      response = sm.describe_secret(
      SecretId=arn
      )
      print(json.dumps(response,indent=4,sort_keys=True,default=str))

      response = sm.update_secret(
          SecretId=arn,
          Description='test2',
          KmsKeyId="fc2e872c-846e-480a-8ffe-bea7067ed8a7",
          SecretString=json.dumps({
          "engine": "mongo",
          "host": "vendorportaldbcluster-6pycmgfxywty.cluster-cfwafydn4lat.ap-southeast-2.docdb.amazonaws.com",
          "port": 21010,
          "ssl": "True",
          "dbClusterIdentifier": "vendorportaldbcluster-6pycmgfxywty",
          "username": "onee",
          "password": "twoo"
          }),
      )

      print("50*|")
      arn=response["ARN"]
      response = sm.describe_secret(
        SecretId=arn
        )
      print(json.dumps(response,indent=4,sort_keys=True,default=str))
