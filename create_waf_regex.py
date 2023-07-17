import sys
import boto3

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

def get_change_token_waf():
    '''
    get Change tokens to ensure application doesn't submit conflicting requests to AWS WAF
    '''
    response = WAF.get_change_token()
    print(f"token is: {response['ChangeToken']}")
    return response['ChangeToken']

def create_regex_pattern_set_waf(env):
    '''
    Creates a RegexPatternSet
    inserts or deletes RegexPatternString objects in a RegexPatternSet
    '''
    #change_token=get_change_token_waf()
    marker = None
    flag = 0 
    pattern=check_if_regex_pattern_set_exists('RegexOpenCostingXssFalsePositive',marker,flag)
    #print(f"pattern: {pattern}---{type(pattern)}")
    if not pattern['flag']:
        response = WAF.create_regex_pattern_set(
            Name='RegexOpenCostingXssFalsePositive',
            ChangeToken=get_change_token_waf()
        )
        regex_pattern_set_id= response['RegexPatternSet']['RegexPatternSetId']
        print(f"regex_pattern_set_id: {regex_pattern_set_id}")
    else:      
        regex_pattern_set_id=pattern['id']

    response = WAF.update_regex_pattern_set(
        RegexPatternSetId=regex_pattern_set_id,
        Updates=[
            {
                'Action': 'INSERT',
                'RegexPatternString': '<?.*`'
            },
        ],
        ChangeToken=get_change_token_waf()
    )
    print("update regex pattern set updated")

    marker = None
    flag = 0
    match=check_if_regex_match_set_exists('RegexOpenCostingXssFalsePositive',marker,flag)
    #if not match['flag']:        
    #create_regex_match_set_waf(pattern['id'],env)
    create_regex_match_set_waf(match,env,regex_pattern_set_id)

def create_regex_match_set_waf(match,env,regex_pattern_set_id):
    '''
    create and update regex match set 
    '''
    if not match['flag']:
        resp_create_regex_match_set = WAF.create_regex_match_set(
            Name='RegexOpenCostingXssFalsePositive',
            ChangeToken=get_change_token_waf()
        )
        regex_match_set_id= resp_create_regex_match_set['RegexMatchSet']['RegexMatchSetId']
    else:
        regex_match_set_id=match['id']

    store_regex_match_setid_ssm_store(env,regex_match_set_id)

    resp_update_regex_match_set = WAF.update_regex_match_set(
        RegexMatchSetId=regex_match_set_id,
        Updates=[
            {
                'Action': 'INSERT',
                'RegexMatchTuple': {
                    'FieldToMatch': {'Type': 'BODY'},
                    'TextTransformation': 'NONE',
                    'RegexPatternSetId': regex_pattern_set_id
                }
            },
        ],
        ChangeToken=get_change_token_waf()
    )
    print("Updated Regex Set Match")

def check_if_regex_pattern_set_exists(regex_name,marker,flag):
    '''
    checks if regex exits
    '''
    paginator = WAF.get_paginator('list_regex_pattern_sets')
    response_iterator = paginator.paginate( 
        PaginationConfig={
            'PageSize': 30,
            'StartingToken': marker
        }
    )
    for page in response_iterator:
        #print(f"Next Page : {page}")
        for i in range(len(page['RegexPatternSets'])):            
            if page['RegexPatternSets'][i]['Name'] == regex_name:
                resp_regex_pattern = WAF.get_regex_pattern_set(RegexPatternSetId=page['RegexPatternSets'][i]['RegexPatternSetId'])
                print(f"Found regex patten set {resp_regex_pattern}")
                print("No action needed.")
                flag=1
                _opt={ 'flag': flag , 'id':page['RegexPatternSets'][i]['RegexPatternSetId']}
                return _opt
    _opt={ 'flag': flag , 'id': 'null'}
    return _opt

def check_if_regex_match_set_exists(regex_name,marker,flag):
    '''
    checks if regex exits
    '''
    paginator = WAF.get_paginator('list_regex_match_sets')
    response_iterator = paginator.paginate( 
        PaginationConfig={
            'PageSize': 30,
            'StartingToken': marker
        }
    )
    for page in response_iterator:
        #print(f"Next Page : {page}")
        for i in range(len(page['RegexMatchSets'])):            
            if page['RegexMatchSets'][i]['Name'] == regex_name:
                resp_match=WAF.get_regex_match_set(RegexMatchSetId=page['RegexMatchSets'][i]['RegexMatchSetId'])
                print(f"Regex match-->  {resp_match['RegexMatchSet']} Found...No action needed. exiting!!!")
                flag=1
                _opt={ 'flag': flag , 'id':page['RegexMatchSets'][i]['RegexMatchSetId']}
                return _opt
    _opt={ 'flag': flag , 'id': 'null'}
    return _opt

def store_regex_match_setid_ssm_store(env,value):
    '''
    Store regex_patter_set_id for cft use
    '''
    SSM.put_parameter(
        Name='/'+env+'/opencosting/regex_match_set_id',
        Description='stores regex_match_set_id for use in CFN',
        Value=value,
        Type='String',        
        Overwrite=True,
        Tier='Standard',        
        DataType='text'
    )
    tag_ssm_paramter(env)

def tag_ssm_paramter(env):
    '''
    tag ssm parameter
    '''
    SSM.add_tags_to_resource(
        ResourceType='Parameter',
        ResourceId='/'+env+'/opencosting/regex_match_set_id',
        Tags=[
                {
                    'Key': 'Billing',
                    'Value': 'Opencosting'
                },
                {
                    'Key': 'Owner',
                    'Value': 'Opencosting'
                }
        ]
    )

if __name__ == '__main__':
    aws_environment=sys.argv[1]    
    ACCOUNT_ID=get_aws_account(aws_environment)
    assumed_session= assumed_role_session('arn:aws:iam::'+ACCOUNT_ID+':role/infra-cfnrole-opencosting-nonprivileged')
    WAF = assumed_session.client('waf', region_name='us-east-1')
    SSM = assumed_session.client('ssm', region_name='ap-southeast-2') 

    create_regex_pattern_set_waf(aws_environment)




