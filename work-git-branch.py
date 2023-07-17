import json
import requests
from datetime import datetime

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
        print(f'\n This was the response code: {response_status}')
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
    response_status = response.status_code
    if response_status > 201:
        print(f'\n This was the response code: {response_status}')
        exit()

    json = response.json()

    return json 

def get_branch_sha(gh_user, gh_token):
	'''
		Input the FULL repo name in the owner/repo_name format. Ex: magento/knowledge-base
		Defaults to master branch. If you don't want to use the master branch, use a different argument.
	'''

	url = f'https://api.github.com/repos/KmartAU/vendorportal-github-pr-request/branches/main'
	response =gh_get_request(gh_user, gh_token, url)
	sha = response.json_all['commit']['sha']
	return sha

def create_new_branch(gh_user, gh_token, master_branch_sha):
	now = str(datetime.now()).replace(' ', '__').replace(':', '-').replace('.', '')
	new_sync_branch = f'new_branch_{now}'
	url = f"https://api.github.com/repos/KmartAU/vendorportal-github-pr-request/git/refs"

	data = {
		"ref": f'refs/heads/{new_sync_branch}',
		"sha": master_branch_sha
	}

	data = json.dumps(data)

	response =gh_post_request(gh_user, gh_token, url, data)

	return response

def main():
	gh_user = input(f"Input your GH username: \n")
	gh_token = input(f"Input your GH token: \n")
	sha = get_branch_sha(gh_user, gh_token)
	new_sync_branch = create_new_branch(gh_user, gh_token, sha)
	print(new_sync_branch)

if __name__ == '__main__':
	main()