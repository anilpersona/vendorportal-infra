
import sys
import boto3
import json
import os
from pymongo import MongoClient, errors
import botocore
from botocore.config import Config

try:
  proxy=os.environ['PROXY']
  proxy_uri=proxy.split('//')[1]
except Exception as e:
  print("Proxy is not set")
  proxy_uri=None
  proxy=None
try:
  region=os.environ['REGION']
except KeyError as e:
  print("Region is not set, using default Sydney")
  region="ap-southeast-2"
try:
  adm_arn=os.environ['ARN']
except KeyError as e:
  print("adm_arn is not set")
  sys.exit(1)
try:
  environment = os.environ['ENVIRONMENT']
except KeyError as e:
  print("Environment is not set")
try:
  kms_key = os.environ['KMS_KEY']
except KeyError as e:
  print("KMS Key is not set")
try:
  sns_topic = os.environ['SNS_TOPIC']
except KeyError as e:
  print("sns_topic is not set")

try:
  enc_slack_hook = os.environ['SLACK_HOOK']
except KeyError as e:
  print("enc_slack_hook is not set")  
try:
  project = os.environ['PROJECT']
except KeyError as e:
  print("project is not set")
  project="sourcing"
configg=Config(
  connect_timeout=10,
  read_timeout=200,
  region_name=region,
  retries={'max_attempts': 2},
  proxies={'https': proxy_uri,'http': proxy_uri},
) 

client_conf={
    "SNS":boto3.client('sns', config=configg),
    "SSM":boto3.client('ssm', config=configg),
    "DOCDB":boto3.client('docdb', config=configg),    
    "SM":boto3.client('secretsmanager', config=configg)    
}  
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

def get_docdb_conn():
  '''
  Return DocumentDB connection Dictionary
  Exit if Get fails
  
  Arg:
      None
  Raises:
      ClientError: If there is some error while calling ssm api
      Exception: Any other error
  '''

  try:
    client = client_conf["SSM"]
    docdb_host=get_ssm(client,"/vendorportal/docdb_endpoint")
    docdb_port=get_ssm(client,"/vendorportal/docdb_port")
    _conn_dict = {
      "host": docdb_host,
      "port": int(docdb_port)
    }
    return _conn_dict
  except botocore.exceptions.ClientError as e:
    print(f"botocore:{e}")
    sys.exit(1)
  except Exception as e:
    print(f"generic:{e}")
    sys.exit(1)
  
def lambda_handler(event, context):
    """Secrets Manager MongoDB Handler

    This handler uses the single-user rotation scheme to rotate a DocumentDB user credential. 
    This rotation scheme logs into the database as the AdminUser and rotates a user's password, immediately invalidating the user's
    previous password.

    The Secret SecretString is expected to be a JSON string with the following format:
    {        
        'host': <required: instance host name>,
        'username': <required: username>,
        'password': <required: password>        
    }

    Args:
        event (dict): Lambda dictionary of event parameters. These keys must include the following:
            - SecretId: The secret ARN or identifier
            - ClientRequestToken: The ClientRequestToken of the secret version
            - Step: The rotation step (one of createSecret, setSecret, testSecret, or finishSecret)

        context (LambdaContext): The Lambda runtime information

    Raises:
        ResourceNotFoundException: If the secret with the specified arn and stage does not exist
        ValueError: If the secret is not properly configured for rotation
        KeyError: If the secret json does not contain the expected keys
    """

    arn = event['SecretId']
    token = event['ClientRequestToken']
    step = event['Step']

    service_client = client_conf['SM']   
    metadata = service_client.describe_secret(SecretId=arn)
    # print_msg("current staged versions",metadata['VersionIdsToStages'])

    if "RotationEnabled" in metadata and not metadata['RotationEnabled']:
        print(f"Secret {arn} is not enabled for rotation")
        raise ValueError(f"Secret {arn} is not enabled for rotation")
    versions = metadata['VersionIdsToStages']
    if token not in versions:
        print(f"Secret version {token} has no stage for rotation of secret {arn}.")
        raise ValueError(f"Secret version {token} has no stage for rotation of secret {arn}.")
    if "AWSCURRENT" in versions[token]:
        print(f"Secret version {token} already set as AWSCURRENT for secret {arn}.")
        return
    elif "AWSPENDING" not in versions[token]:
        print(f"Secret version {token} not set as AWSPENDING for rotation of secret {arn}.")
        raise ValueError(f"Secret version {token} not set as AWSPENDING for rotation of secret {arn}.")

    
    if step == "createSecret":
        print_msg("Start: Create Secret")
        create_secret(service_client, arn, token)
        print_msg("End: Create Secret")      
    elif step == "setSecret":
        print_msg("Start: Set Secret")
        set_secret(service_client, arn, token)
        print_msg("End: Set Secret")

    elif step == "testSecret":
        print_msg("Start: Test Secret")
        test_secret(service_client, arn, token)
        print_msg("End: Test Secret")

    elif step == "finishSecret":
        print_msg("Start: Finish Secret")      
        finish_secret(service_client, arn, token)
        print_msg("End: Finish Secret")

    else:
        print(f"lambda_handler: Invalid step parameter {step} for secret {arn}")
        raise ValueError(f"Invalid step parameter {step} for secret {arn}")


def create_secret(service_client, arn, token):
    """Generate a new secret

    This method first checks for the existence of a secret for the passed in token. If one does not exist, it will generate a
    new secret and put it with the passed in token.

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version

    Raises:
        ValueError: If the current secret is not valid JSON

        KeyError: If the secret json does not contain the expected keys

    """    
    current_dict = get_secret_dict(service_client, arn, "AWSCURRENT")
    print("Current version secret exists")    
    try: 
        get_secret_dict(service_client, arn, "AWSPENDING", token)
        print(f"Successfully retrieved secret for {arn}.")
    except service_client.exceptions.ResourceNotFoundException:        
        print_msg("creating new secret")
        exclude_characters = os.environ['EXCLUDE_CHARACTERS'] if 'EXCLUDE_CHARACTERS' in os.environ else '/@"\'\\()*+,-.:;<=>?[]^_`\{\}\/&%'        
        passwd = service_client.get_random_password(ExcludeCharacters=exclude_characters)
        current_dict['password'] = passwd['RandomPassword']
        service_client.put_secret_value(SecretId=arn, ClientRequestToken=token, SecretString=json.dumps(current_dict), VersionStages=['AWSPENDING'])
        print(f"Successfully put secret for ARN {arn} and version {token}.")

def set_secret(service_client, arn, token):
    """Set the pending secret in the Docdb

    This method tries to login to the database with the AWSPENDING secret and returns on success.
    If that fails, it  tries to login with the AWSCURRENT and AWSPREVIOUS secrets. 
    If either one succeeds, it sets the AWSPENDING password
    as the user password in the database. Else, it throws a ValueError.

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version

    Raises:
        ResourceNotFoundException: If the secret with the specified arn and stage does not exist

        ValueError: If the secret is not valid JSON or valid credentials are found to login to the database

        KeyError: If the secret json does not contain the expected keys

    """
    
    try:
        previous_dict = get_secret_dict(service_client, arn, "AWSPREVIOUS")
        # print_msg("previous_dict",previous_dict)
        print("AWSPREVIOUS Exists")
    except (service_client.exceptions.ResourceNotFoundException, KeyError):
        print("AWSPREVIOUS NotFound")
        previous_dict = None
    current_dict = get_secret_dict(service_client, arn, "AWSCURRENT")
    # print_msg("current_dict",current_dict)
    pending_dict = get_secret_dict(service_client, arn, "AWSPENDING", token)
    # print_msg("pending_dict",pending_dict)

    # First try to login with the pending secret, if it succeeds, return
    print("DB Login with AWSPENDING")
    db_client = get_connection(pending_dict)
    if db_client:
        # conn.logout()
        db_client.close()
        print(f"AWSPENDING secret is already set as password in MongoDB for secret arn {arn}")
        return

    # Make sure the user from current and pending match
    if current_dict['username'] != pending_dict['username']:
        print(f"setSecret: Attempting to modify user {pending_dict['username']} other than current user {current_dict['username']}")
        raise ValueError(f"Attempting to modify user {pending_dict['username']} other than current user {current_dict['username']}")

    # Make sure the host from current and pending match
    if current_dict['host'] != pending_dict['host']:
        print(f"setSecret: Attempting to modify user for host {pending_dict['username']} other than current host {current_dict['username']}")
        raise ValueError(f"Attempting to modify user for host {pending_dict['username']} other than current host {current_dict['username']}")

    # Now try the current password
    print("DB Login with AWSCURRENT")
    db_client = get_connection(current_dict)

    # If both current and pending do not work, try previous
    if not db_client and previous_dict:
        db_client = get_connection(previous_dict)
        # Make sure the user/host from previous and pending match
        if previous_dict['username'] != pending_dict['username']:
            print(f"setSecret: Attempting to modify user {pending_dict['username']} other than previous valid user {previous_dict['username']}")
            raise ValueError(f"Attempting to modify user {pending_dict['username']} other than previous valid user {previous_dict['username']}")
        if previous_dict['host'] != pending_dict['host']:
            print(f"setSecret: Attempting to modify user for host {pending_dict['host']} other than previous host {previous_dict['host']}")
            raise ValueError(f"Attempting to modify user for host {pending_dict['host']} other than previous host {previous_dict['host']}")

    # If we still don't have a connection, raise a ValueError
    if not db_client:
        print(f"setSecret: Unable to log into database with previous, current, or pending secret of secret arn {arn}")
        raise ValueError(f"Unable to log into database with previous, current, or pending secret of secret arn {arn}")
        #RAISE ALARM TBD

    # Now set the password to the pending password
    try:
        print(f"Update using Admin user")
        admin_dict=get_secret_dict(service_client, adm_arn, "AWSCURRENT")
        db_client=get_connection(admin_dict)
        conn=db_client.admin
        resp=conn.command({
                              "updateUser": pending_dict["username"],
                              "pwd": pending_dict["password"]
                            })
        print(f"Successfully set password for user {pending_dict['username']} in MongoDB for secret arn {arn}")
    except errors.PyMongoError:
        print(f"setSecret: Error encountered when attempting to set password in database for user {pending_dict['username']}")
        raise ValueError(f"Error encountered when attempting to set password in database for user {pending_dict['username']}")
    finally:
        db_client.close()

def test_secret(service_client, arn, token):
    """Test the pending secret against the database

    This method tries to log into the database with the secrets staged with AWSPENDING and runs
    a permissions check to ensure the user has the corrrect permissions.

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version

    Raises:
        ResourceNotFoundException: If the secret with the specified arn and stage does not exist

        ValueError: If the secret is not valid JSON or valid credentials are found to login to the database

        KeyError: If the secret json does not contain the expected keys

    """
    print("DB Login with AWSPENDING")
    pending_dict = get_secret_dict(service_client, arn, "AWSPENDING", token)
    db_client = get_connection(pending_dict)    
    if db_client:
        # This is where the lambda will validate the user's permissions. Uncomment/modify the below lines to
        # tailor these validations to your needs
        try:
            conn=db_client["admin"]
            resp=conn.command("buildinfo")
            print_msg("buildinfo",{"MongoVersion":resp["version"]})
        finally:
            db_client.close()
        print(f"testSecret: Successfully signed into MongoDB with AWSPENDING secret in {arn}")
        return
    else:
        print(f"testSecret: Unable to log into database with pending secret of secret ARN {arn}")
        raise ValueError(f"Unable to log into database with pending secret of secret ARN {arn}")


def finish_secret(service_client, arn, token):
    """Finish the rotation by marking the pending secret as current

    This method finishes the secret rotation by staging the secret staged AWSPENDING with the AWSCURRENT stage.

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version

    """
    # First describe the secret to get the current version
    metadata = service_client.describe_secret(SecretId=arn)
    current_version = None
    for version in metadata["VersionIdsToStages"]:
        if "AWSCURRENT" in metadata["VersionIdsToStages"][version]:
            if version == token:
                # The correct version is already marked as current, return
                print(f"finishSecret: Version {version} already marked as AWSCURRENT for {arn}")
                return
            current_version = version
            break

    # Finalize by staging the secret version current
    service_client.update_secret_version_stage(SecretId=arn, VersionStage="AWSCURRENT", MoveToVersionId=token, RemoveFromVersionId=current_version)
    print(f"finishSecret: Successfully set AWSCURRENT stage to version {token} for secret {arn}.")


def get_connection(secret_dict):
    """Gets a connection to MongoDB from a secret dictionary

    This helper function uses connectivity information from the secret dictionary to initiate
    connection attempt(s) to the database. Will attempt a fallback, non-SSL connection when
    initial connection fails using SSL and fall_back is True.

    Args:
        secret_dict (dict): The Secret Dictionary

    Returns:
        Connection: The pymongo.database.Database object if successful. None otherwise

    Raises:
        KeyError: If the secret json does not contain the expected keys

    """
    conn_dict=get_docdb_conn()
    conn = connect_and_authenticate(conn_dict,secret_dict)    
    return conn

def connect_and_authenticate(conn_dict,secret_dict):
    """Attempt to connect and authenticate to a MongoDB instance

    This helper function tries to connect to the database using connectivity info passed in.
    If successful, it returns the connection, else None

    Args:
        - secret_dict (dict): The Secret Dictionary
        - port (int): The databse port to connect to
        - dbname (str): Name of the database
        - use_ssl (bool): Flag indicating whether connection should use SSL/TLS

    Returns:
        Connection: The pymongo.database.Database object if successful. None otherwise

    Raises:
        KeyError: If the secret json does not contain the expected keys

    """
    # Try to obtain a connection to the db
    try:        
        client = MongoClient(            
            host=conn_dict['host'],
            port=conn_dict['port'],
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=9000,
            ssl=True,
            tlsCAFile='rds.pem',
            authSource='admin',
            replicaSet="rs0",
            readPreference="secondaryPreferred",
            retryWrites=False,
            authMechanism="SCRAM-SHA-1",
            username=secret_dict['username'],
            password=secret_dict['password']
        )               
        resp=client.admin.command('usersInfo', secret_dict['username'])
        print(f"Successfully established connection")
        print_msg("Info",{
          "user":resp["users"][0]["user"],
          "roles": resp["users"][0]["roles"]
        })
        return client
    except errors.ServerSelectionTimeoutError as e:
        print(f"ServerSelectionTimeoutError: {e}")
        return None
    except errors.PyMongoError as e:
        print(f"Pymongo error: {e}")        
        return None
    except Exception as e:
        print(f"Generic Exception: {e}")        
        return None

def get_secret_dict(service_client, arn, stage, token=None):
    """Gets the secret dictionary corresponding for the secret arn, stage, and token

    This helper function gets credentials for the arn and stage passed in and returns the dictionary by parsing the JSON string

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version, or None if no validation is desired

        stage (string): The stage identifying the secret version

    Returns:
        SecretDictionary: Secret dictionary

    Raises:
        ResourceNotFoundException: If the secret with the specified arn and stage does not exist

        ValueError: If the secret is not valid JSON

    """
    required_fields = ['host', 'username', 'password']

    # Only do VersionId validation against the stage if a token is passed in
    if token:
        secret = service_client.get_secret_value(SecretId=arn, VersionId=token, VersionStage=stage)
    else:
        secret = service_client.get_secret_value(SecretId=arn, VersionStage=stage)    
    plaintext = secret['SecretString']    
    secret_dict = json.loads(plaintext)  
    return secret_dict

def get_pending_version(arn,client):
  
  response = client.describe_secret(SecretId=arn)
  stages=response['VersionIdsToStages']

  for version in stages:
    for label in  stages[version]:
      if "AWSPENDING" == label:
        return version

def rotate(arn,client):
  try:
    response = client.rotate_secret(
      SecretId=arn,    
      RotateImmediately=True
    )
  except Exception as e:
    print("Error while calling rotate secret api",e)    

if __name__ == "__main__":
  print(f"***Initialize***")
  arn="arn:aws:secretsmanager:ap-southeast-2:187628286232:secret:/vendorportal/secret/user3-bYBkXh"

  sm = client_conf["SM"]
  rotate(arn,sm)
  token=get_pending_version(arn,sm)
  if token:
    clientToken=token
  else:
    print_msg("No pending version found")
    sys.exit(1)
  
  elist=["createSecret", "setSecret", "testSecret", "finishSecret"]
  for step in elist:
    event={
        'ClientRequestToken': clientToken,
        'SecretId': 'arn:aws:secretsmanager:ap-southeast-2:187628286232:secret:/vendorportal/secret/user3-bYBkXh',
        'Step': step        
    }
    lambda_handler(event,context=None)


