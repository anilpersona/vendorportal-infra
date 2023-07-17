'''
Retrieve Webacl id from stack output and assocaite the logging configuration with firehose
'''
import sys
import boto3
import time

def assumed_role_session(role_arn: str):
    '''
    change role
    '''
    role = boto3.client('sts').assume_role(RoleArn=role_arn, RoleSessionName='switch-role')
    credentials = role['Credentials']
    aws_access_key_id = credentials['AccessKeyId']
    aws_secret_access_key = credentials['SecretAccessKey']
    aws_session_token = credentials['SessionToken']
    return boto3.session.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token)
    
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
    else:
        print(f"cannot determine account for {aws_env}") 
        sys.exit(1)
    return acc

def get_stack_output_vars(cft_name,*args):
    '''
    Given a stack name , return a dict of output keys and values
    '''    
    response = CFN.describe_stacks(StackName=cft_name)
    output_list=response['Stacks'][0]['Outputs']
    _output_dict={}
    for item in output_list:      
        _output_dict[item['ExportName']]=item['OutputValue']
    return _output_dict
        
      

def put_webacl_log_config(waf_arn, firehose_arn):
    '''
    Associate Webacl with Firehose   
    '''
    response = WAF.put_logging_configuration(
        LoggingConfiguration={
            'ResourceArn': waf_arn,
            'LogDestinationConfigs': [firehose_arn],
            'RedactedFields': []
        }
    )

if __name__ == '__main__':
    aws_environment=sys.argv[1]
    project=sys.argv[2]
    waf_stack_name=project+"-stack-waf-"+aws_environment
    firehose_stack_name=project+"-stack-firehose-"+aws_environment
    ACCOUNT_ID=get_aws_account(aws_environment)
    assumed_session= assumed_role_session('arn:aws:iam::'+ACCOUNT_ID+':role/infra-cfnrole-'+project+'-nonprivileged')
    WAF = assumed_session.client('wafv2', region_name='us-east-1')
    CFN = assumed_session.client('cloudformation', region_name='us-east-1')
    
    waf_export_dict=get_stack_output_vars(waf_stack_name)
    firehose_export_dict=get_stack_output_vars(firehose_stack_name)    
    put_webacl_log_config(waf_export_dict[waf_stack_name+'::WebACLArn'],firehose_export_dict[firehose_stack_name+'::DeliveryStreamArn'])

