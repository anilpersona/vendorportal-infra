'''
Update prefix list attached for public alb
'''
import sys
import boto3
import json
import logging
import urllib.request, urllib.error, urllib.parse
import os
from time import sleep
import botocore

url='https://ip-ranges.amazonaws.com/ip-ranges.json'
pf_list=os.environ['PREFIX_LIST_ID']

def get_ip_groups_json(url):
    '''
    gets ip json dump from aws-ip-range url
    '''
    logging.info("Updating from " + url)
    response = urllib.request.urlopen(url)
    ip_json = response.read()
    return ip_json

def get_new_ips_list( _ip_json , service):
    '''
    returns latest cloudfront ip from the json dump
    '''
    _service_range_list = list()    
    for prefix in _ip_json['prefixes']:
        if prefix['service'] == service:
            _service_range_list.append(prefix['ip_prefix'])
    
    logging.info(('Found ' + service + ' ranges: ' + str(len(_service_range_list))))
    return _service_range_list 

def get_prefix_list_version(client):
  '''
  list existing pf list's version needed for updating a pf
  '''
  response = client.describe_managed_prefix_lists(      
      PrefixListIds=[pf_list]
  )
  return response['PrefixLists'][0]['Version']

def get_old_ips_list(client):
  '''
  gets all the current entries from prefix-list
  '''
  existing_ip_list=[]
  flag=1
  marker = None
  while flag:
      paginator = client.get_paginator('get_managed_prefix_list_entries')
      response_iterator = paginator.paginate(
        PrefixListId=pf_list,
        PaginationConfig={
            'MaxItems': 100,
            'PageSize': 100,
            'StartingToken': marker
        }
      )
      for page in response_iterator:
          for i in range(len(page['Entries'])):
              existing_ip_list.append(page['Entries'][i]['Cidr'])
          try:
              marker = page['NextToken']        
          except KeyError:
              flag=0
              break   
  return existing_ip_list
    
def get_updations_lists(old_list, new_list):
    '''
    returns revoke list and update list
    '''
    revoke_list=list(set(old_list)-set(new_list))
    add_list=list(set(new_list)-set(old_list))
    _output={
        'revoke_list': revoke_list,
        'add_list': add_list,
        'clear_list': old_list
    }
    return _output


def modify_prefix_list_entries(client,pf_version,update_dict,action):
    '''
    add or revoke entries from prefix
    '''
    try:
        if action == 'revoke':
            response = client.modify_managed_prefix_list(
                PrefixListId=pf_list,
                CurrentVersion=pf_version,
                RemoveEntries=update_dict
            )
        elif action == 'add':
            response = client.modify_managed_prefix_list(
                PrefixListId=pf_list,
                CurrentVersion=pf_version,
                AddEntries=update_dict
            )
        else:
            print('no update needed')
        status='success'
    except botocore.exceptions.ClientError as error:
        status='failed. Reason: '+ str(error)
    return status    
        

def get_prefix_list_entries(_input_list,action):
    '''
    return an update-entry dictionary for pf udpate
    '''
    _output = list()
    for i in _input_list:
        if action == 'add':
            _output.append({'Cidr': i,'Description': 'lambda-cf'})
        else:
            _output.append({'Cidr': i})
    #logging.info(('Found ' + service + ' ranges: ' + str(len(_service_ranges))))
    return _output        

def update_pf(client,_ip_list,action):
  '''
  validate and paginate input to modify function
  '''
  start=0
  stop=100
  step=100
  print(f"Action: {action} {len(_ip_list)} IPs \n IPs:{_ip_list}")
  for i in range(int(len(_ip_list)/step) + 1):
    current_range=_ip_list[start:stop]
    if (current_range):
        latest_pf_version=get_prefix_list_version(client)
        prefix_entries=get_prefix_list_entries(current_range,action)
        status=modify_prefix_list_entries(client,latest_pf_version,prefix_entries,action)
        start=stop
        stop=stop+step
        print(f"Result: {status} | {action} {len(current_range)} IPs")
    else:
      break
    sleep(2)

def handler(event, context):
  EC2 = boto3.client('ec2')  
  ip_ranges=json.loads(get_ip_groups_json(url))
  new_cf_ranges_list=get_new_ips_list(ip_ranges,'CLOUDFRONT')
  old_pf_ranges_list=get_old_ips_list(EC2)
  update_dict=get_updations_lists(old_pf_ranges_list,new_cf_ranges_list)
  add_list=update_dict['add_list']
  revoke_list=update_dict['revoke_list']
  
  update_pf(EC2,revoke_list,'revoke')
  update_pf(EC2,add_list,'add')
