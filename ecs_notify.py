'''
Notify on ECS task failure
'''
from base64 import b64decode
import sys
import boto3
import json
import requests
import urllib.request, urllib.error, urllib.parse
import os
from time import sleep
from botocore.config import Config
import smtplib
import email
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def decrypt(client,key_id,val,env_context):
  '''
  Take a value and decrypt it
  '''
  _val=""
  try:
    response = client.decrypt(
    CiphertextBlob=b64decode(val),
    KeyId=key_id,
    EncryptionContext={'env': env_context},
    EncryptionAlgorithm='SYMMETRIC_DEFAULT'
    )
    _val=response['Plaintext'] #bytes
  except Exception as e:
    print_msg("Exception during decryption",{"error":str(e)})
  return _val
def print_msg(msg,*args):
    '''
    print status
    '''      
    print(f"\n{80*'-'}\n\n{msg}!")
    if len(args) == 1 and {} in args:
        print("No Items")
    for item in args:
        for key,value in item.items():
            print(f"\n{key} : {value}")
    print(f"\n{80*'-'}\n")
def send_mail(payload,to_email,from_email):
  '''
  send mail to test box
  '''
  HOST = "appsmtpgw.core.kmtltd.net.au"
  SUBJECT = "ECS TASK STOPPED Alert"
  TO = to_email
  FROM = from_email
  # text = "Unexpected ecs task termination, please find the details below"
  
  
  message = MIMEMultipart()
  message["From"] = FROM
  message["To"] = TO
  message["Subject"] = SUBJECT
  # BODY = text

  BODY = "\r\n".join(( 
                      "Hello Devs!\n\n",
                      "Name: %s\n" % payload["Name"],
                      "Account: %s\n" % payload["Account"],                      
                      "Environment: %s\n" % payload["Environment"],
                      "StoppedAt: %s\n" % payload["StoppedAt"],
                      "StoppedReason: %s\n" % payload["StoppedReason"],
                      "Reason: %s\n" % payload["Reason"],
                      "\n Regards, \nOSB Team"))
  message.attach(MIMEText(BODY, "plain"))
  text = message.as_string()
  server = smtplib.SMTP(HOST)
  server.connect(HOST,25)
  server.sendmail(FROM, [TO], text)
  server.quit()
  print_msg("email sent",{"To" : to_email})

def parse_payload(event_obj):
  
  for record in event_obj["Records"]:
    payload_obj=json.loads(record["Sns"]["Message"])
    
    container_length=len(payload_obj["detail"]["containers"])
    if container_length > 0:
      _reason=payload_obj["detail"]["containers"][0].get("reason","empty")
      _name=payload_obj["detail"]["containers"][0].get("name","empty")
    else:
      _reason="empty"  
      _name=payload_obj["detail"]['taskDefinitionArn'].split("/")[1]
    _account=payload_obj.get("account","empty")
    _stopped_at=payload_obj["detail"].get("stoppedAt","empty")
    _stopped_reason=payload_obj["detail"].get("stoppedReason","empty")

    parsed_payload={
      "Name": _name,
      "Account": _account,
      "Environment": os.environ.get('AWS_ENV'),
      "StoppedAt": _stopped_at,
      "StoppedReason": _stopped_reason,
      "Reason": _reason
    }
    slack_payload=f'''
      *Name*: `{_name}`\n
      *Account*: `{_account}`\n
      *Environment*: `{os.environ.get('AWS_ENV')}`\n
      *StoppedAt*: `{_stopped_at}`\n
      *StoppedReason*: `{_stopped_reason}`\n
      *Reason*: `{_reason}`
    '''

  return parsed_payload,slack_payload
def send_slack(url,message,aws_env,proxy=None):
  '''
  send slack message
  '''
  aws_env=aws_env.upper()
  proxies = {
  "http": proxy,
  "https": proxy
  }
  slack_data=  {
	  "blocks": [
      {
			"type": "divider"
		  },
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": " :redsiren: AWS: "+aws_env +" Notification - "+message
        }
		  }
	  ]
  }
  byte_length = str(sys.getsizeof(slack_data))
  headers = {'Content-Type': "application/json", 'Content-Length': byte_length}
  response = requests.post(url, data=json.dumps(slack_data), headers=headers,proxies=proxies)
  if response.status_code != 200:
      raise Exception(response.status_code, response.text)

def handler(event, context):
  # event=json.loads(event['body'])
  aws_env=os.environ.get('AWS_ENV')
  try:
    proxy=os.environ['PROXY']
    proxy_uri=proxy.split('//')[1]
  except Exception as e:
    print_msg("Error in obtaining proxy",{"error":str(e)})
    proxy=None
    proxy_uri=None
  try:
    region=os.environ['REGION']
  except KeyError as e:
    print_msg("Region is not set, using default Sydney")
    region="ap-southeast-2"

  try:
    environment = os.environ['ENVIRONMENT']
  except KeyError as e:
    print_msg("Environment is not set")
  try:
    kms_key = os.environ['KMS_KEY']
  except KeyError as e:
    print_msg("KMS Key is not set")
  enc_slack_hook = os.environ['SLACK_HOOK']

  configg=Config(
      connect_timeout=10,
      read_timeout=200,
      region_name=region,
      retries={'max_attempts': 2},
      proxies={'https': proxy_uri,'http': proxy_uri}
  )  
  kms_client = boto3.client('kms', config=configg)  
  payload,slack_text=parse_payload(event)
  env_context="notify"
  slack_hook=decrypt(kms_client,kms_key,enc_slack_hook,env_context)
  if not (slack_hook and len(slack_hook) !=0):
    print_msg("slack hook empty")
  if aws_env == "prod":
    slack_message="@here *ECS Task Stopped* "+"Details"+"\n"+">>>"+slack_text    
  else:
    slack_message="*ECS Task Stopped* "+"Details"+"\n"+">>>"+slack_text    
  send_slack(slack_hook,slack_message,aws_env,proxy)
  send_mail(payload,os.environ["TO_EMAIL"],os.environ["FROM_EMAIL"])

if __name__ == "__main__":
  event={"a":"b"}
  handler(event,"test")