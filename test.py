import json
import boto3

if __name__ =="__main__":

      ssm=boto3.client("ssm",region_name="ap-southeast-2")
      ssm.put_parameter(
        Name="/vendorportal/seceret/test",
        Description="secret",
        Value="11123",
        Type='SecureString',
        Overwrite=True,           
        Tier='Standard',
        # KeyId="fc2e872c-846e-480a-8ffe-bea7067ed8a7"
        KeyId="f106b459-f74c-4543-b34a-6e580436e93f"
      )
      response = ssm.describe_parameters(
         ParameterFilters=[
            # {
            #     'Key': 'KeyId',
            #     'Values': ['alias/aws/ssm']
            # },
            {
                'Key': 'Name',
                'Values': ['/vendorportal/seceret/test']
            },
        ],
      )
      print(json.dumps(response["Parameters"],indent=4,sort_keys=True,default=str))


