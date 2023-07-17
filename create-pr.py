#!/usr/bin/env python3

import json
import requests
import os
import urllib3

from urllib.request import Request, urlopen
from urllib.parse import urlencode
from json import dumps

from datetime import datetime

from urllib.parse import urlencode
from requests.exceptions import RequestException

WEBHOOK_URL = 'https://hooks.slack.com/services/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'
GITHUB_PULL_URL = ("%s/repos/%s/pulls")
# organization = 'pvlib'
# repository = 'pvlib-python'
# state = 'all'  # other options include 'closed' or 'open'

# page = 1  # initialize page number to 1 (first page)
# dfs = []  # create empty list to hold individual dataframes
# # Note it is necessary to loop as each request retrieves maximum 30 entries
# while True:
#     url = f"https://api.github.com/repos/{organization}/{repository}/pulls?" \
#         f"state={state}&page={page}"
#     dfi = pd.read_json(url)
#     if dfi.empty:
#         break
#     dfs.append(dfi)  # add dataframe to list of dataframes
#     page += 1  # Advance onto the next page

def gh_sesh(user, token):
    s = requests.Session()
    s.auth = (user, token)
    s.headers = {'accept': 'application/vnd.github.v3+json'}
    return s

class GH_Response_Obj:
    def __init__(self, json_all, next_page):
        self.json_all = json_all
        self.next_page = next_page

def gh_get_request(gh_user, gh_token, url):
    s = gh_sesh(gh_user, gh_token)
    response = s.get(url)
    response_status = response.status_code
    if response_status > 200:
        print(f'\n gh_get_request This was the response code: {response_status}')
        exit()

    json = response.json()
    links = response.links

    try:
        next_page = links['next']['url']
    except:
        next_page = None

    full = GH_Response_Obj(json, next_page)

    return full

def gh_post_request(gh_user, gh_token, url, data):
    s = gh_sesh(gh_user, gh_token)
    response = s.post(url, data)
    print(url)
    response_status = response.status_code
    if response_status > 201:
        print(f'\n gh_post_request This was the response code: {response_status}')
        exit()

    json = response.json()

    return json

def get_branch_sha(gh_user, gh_token):
    '''
        Input the FULL repo name in the owner/repo_name format. Ex: magento/knowledge-base
        Defaults to master branch. If you don't want to use the master branch, use a different argument.
    '''
    # url = f'https://api.github.com/repos/{repo_name}/branches/{branch_name}'

    url="https://api.github.com/repos/KmartAU/vendorportal-github-pr-request/branches/main"
    response =gh_get_request(gh_user, gh_token, url)
    print(response)
    sha = response.json_all['commit']['sha']
    return sha 

def create_pull_request(repo_name, title, description, head_branch, base_branch, gh_token):
    """Creates the pull request for the head_branch against the base_branch"""
    git_pulls_api = "https://api.github.com/repos/{0}/pulls".format(
         repo_name)
    headers = {
        "Authorization": "token {0}".format(gh_token),
        "Content-Type": "application/json"}
    data = {
        "title": title,
        "body": description,
        "base": base_branch,
        "head": head_branch,
    }

    r = requests.get(
        git_pulls_api,
        headers=headers,
        data=json.dumps(data))
    output = json.loads(r.text)
    for k,v in output[0].items():
        if k == "html_url":
            return v
    # if not r.ok:
    #     print("Request Failed: {0}".format(r.text))
    if r.status_code == 200:
    #get pull url was successful
      return True
    else:
    #Something went wrong. Oh well.
      return r.status_code
        
def get_pull_request(repo_name,pull,gh_token):
    """Creates the pull request for the head_branch against the base_branch"""
    html_url = "https://api.github.com/repos/{0}/pull/{1}".format(
         repo_name,pull)
    headers = {
        "Authorization": "token {0}".format(gh_token),
        "Content-Type": "application/json"}

    r = requests.post(
        html_url,
        headers=headers)
    print(str(r)+"--------")
    
    # response = requests.post(url)
    if r.status_code == 200:
    #get pull url was successful
      return True
    else:
    #Something went wrong. Oh well.
      return r.status_code

def postSlack(message):
    encoded_data = json.dumps(message).encode('utf-8')
    http = urllib3.PoolManager()
    response = http.request('POST',
        WEBHOOK_URL, body=encoded_data,
        headers={'Content-Type': 'application/json'}
    )
    print(message)
    status_code = response.status
    if status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s'
            % (status_code)
        )
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
    
def main():
    gh_user= "Anil8688"
    gh_token = "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"
    repo_name = "KmartAU/vendorportal-github-pr-request"
    title = "poc"
    description = "please find the pull request"
    head_branch = "test-branch"
    base_branch = "main"
    sha = get_branch_sha(gh_user, gh_token)
    # data = {'text': 'Testing!','url':get_url}
    pull_body = create_pull_request( repo_name,title, description, head_branch, base_branch, gh_token)
    print(pull_body)
    # git_url = get_pull_request(repo_name,pull,gh_token)
    # print(f'{git_url}----')
    data = {'text':pull_body }
    slack = postSlack(data)
    print(slack)
    
        
if __name__ == '__main__':
    	main()   


