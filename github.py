#!/usr/bin/env python3

import sys
import requests
import argparse
import json
import os
from getpass import getpass
import re


class colors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'


#
# Get authorization token
#
def createToken( creds ):
	data = {
		'scopes' : ['repo'],
		'note'   : 'Github CLI'
	}

	url = server + '/authorizations'
	response = requests.post(url, data=json.dumps(data), auth=creds)
	response.encoding = 'UTF-8'

	if response.status_code != 201:
		print('Unable to create token: ' + response.json()['message'])
		sys.exit(1)

	res = response.json()

	return res['token']


def askForCredentials():
	username = input('Username: ')
	password = getpass('Password: ')

	return (username, password)


#
# Store token
#
def storeToken( file, token ):
	file = os.path.expanduser( file )

	path, filename = os.path.split( file )

	if not os.path.exists( path ):
		os.makedirs( path )

	with open( file, "w") as fp:
		fp.write( token )


#
# Get token
#
def retrieveToken( file ):
	file = os.path.expanduser( file )

	if not os.path.exists( file ):
		print('No token available. Please use the auth command.')
		sys.exit(1)

	with open( file, "r") as fp:
		stored_token = fp.readline()

	return stored_token


#
# List releases
#
def listReleases( token ):
	user, repo = get_repo_info()
	url = server + '/repos/{}/{}/releases'.format( user, repo )

	response = requests.get(url, headers={'Authorization': 'token ' + token})
	response.encoding = 'UTF-8'

	if response.status_code != 200:
		print('Unable to list releases')
		sys.exit(1)

	# Print the 5 newest releases
	for id, release in enumerate( response.json()[0:5] ):
		if id == 0:
			print( "{}{} ({}) -> {}{}".format( colors.OKGREEN, release['name'], release['tag_name'], release['tarball_url'], colors.ENDC ) )
		else:
			print( "{} ({}) -> {}".format( release['name'], release['tag_name'], release['tarball_url'] ) )


#
# Get Github user and repository name from current directory
#
def get_repo_info():
	url = os.popen("git config --get remote.origin.url").read()

	if not url:
		print('Current directory is not a valid Git repository')
		sys.exit(1)

	pattern = re.compile('git@github\.com:([a-z]+)\/([a-z-]+)\.git')
	match = pattern.match( url )

	if match:
		user = match.group(1)
		repo = match.group(2)

		return user, repo

	return None


#
# Parse command line parameters
#
parser = argparse.ArgumentParser()
parser.add_argument('command', help='Github command (release)')

if len(sys.argv) == 1:
	parser.print_help(sys.stderr)
	sys.exit(1)

args = parser.parse_args()








server = 'https://api.github.com'
token_file = '~/.github/token'


#
# Authenticate and get new token
#
if args.command == 'auth':
	creds = askForCredentials()
	token = createToken( creds )
	storeToken(token_file, token)
	print('New token stored')


#
# List all releases
#
if args.command == 'list':
	token = retrieveToken(token_file)
	listReleases( token )




