#!/usr/bin/env python3

import sys
import requests
import argparse
import json
import os
import stat
from getpass import getpass
import re


class Colors:
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
def create_token(creds):
    data = {
        'scopes': ['repo'],
        'note': 'Github CLI'
    }

    url = server + '/authorizations'
    response = requests.post(url, data=json.dumps(data), auth=creds)
    response.encoding = 'UTF-8'

    otpheader = response.headers.get('X-GitHub-OTP')

    # Handle login with two-factor authentication
    if response.status_code == 401 and otpheader is not None and 'required' in otpheader:
        otp = input('Enter one-time password: ')

        response = requests.post(url, data=json.dumps(data), auth=creds, headers={'X-GitHub-OTP': otp})
        response.encoding = 'UTF-8'

    if response.status_code != 201:
        print('Unable to create token: ' + response.json()['message'])
        sys.exit(1)

    res = response.json()

    return res['token']


def ask_for_credentials():
    username = input('Username: ')
    password = getpass('Password: ')

    return username, password


#
# Store token
#
def store_token(file, token):
    file = os.path.expanduser(file)

    path, filename = os.path.split(file)

    if not os.path.exists(path):
        os.makedirs(path)

    with open(file, "w") as fp:
        fp.write(token)

    os.chmod(file, stat.S_IRUSR)


#
# Get token
#
def retrieve_token(file):
    file = os.path.expanduser(file)

    if not os.path.exists(file):
        print('No token available. Please use the auth command.')
        sys.exit(1)

    with open(file, "r") as fp:
        stored_token = fp.readline()

    return stored_token


#
# List releases
#
def list_releases(token):
    user, repo = get_repo_info()
    url = server + '/repos/{}/{}/releases'.format(user, repo)

    response = requests.get(url, headers={'Authorization': 'token ' + token})
    response.encoding = 'UTF-8'

    if response.status_code != 200:
        print('Unable to list releases')
        sys.exit(1)

    # Print the 5 newest releases
    for id, release in enumerate(response.json()[0:5]):
        if id == 0:
            print(
                "{}{} ({}) -> {}{}".format(Colors.OKGREEN, release['name'], release['tag_name'], release['tarball_url'],
                                           Colors.ENDC))
        else:
            print("{} ({}) -> {}".format(release['name'], release['tag_name'], release['tarball_url']))


#
# Get Github user and repository name from current directory
#
def get_repo_info():
    url = os.popen("git config --get remote.origin.url").read()

    if not url:
        print('Current directory is not a valid Git repository')
        sys.exit(1)

    pattern = re.compile('git@github\.com:([a-z]+)\/([a-z-]+)\.git')
    match = pattern.match(url)

    if match:
        user = match.group(1)
        repo = match.group(2)

        return user, repo

    return None








#
# Parse command line parameters
#


server = 'https://api.github.com'
token_file = '~/.github/token'


class Github(object):

    def __init__(self):
        parser = argparse.ArgumentParser(
            description='',
            usage='''github <command> [<args>]

The most commonly used github commands are:
  auth        Create new authentication token
  release     List, create or delete releases
''')
        parser.add_argument('command', help='Subcommand to run')

        if len(sys.argv) == 1:
            parser.print_help(sys.stderr)
            sys.exit(1)

        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)

        getattr(self, args.command)()

    def auth(self):
        parser = argparse.ArgumentParser(
            usage='github auth',
            description='Create new authentication token'
        )
        args = parser.parse_args(sys.argv[2:])

        print('Please enter credentials to authenticate')
        creds = ask_for_credentials()
        token = create_token(creds)
        store_token(token_file, token)
        print('New token stored')

    def release(self):
        parser = argparse.ArgumentParser(
            usage='github release <command> [<args>]',
            description='List, create or delete releases'
        )
        parser.add_argument('command', help='Available commands is create, delete and list')
        # parser.add_argument('args', nargs='?')
        parser.add_argument('-n', '--name', help='Release name')
        parser.add_argument('-t', '--tag', help='Tag used in the current release')
        parser.add_argument('-f', '--file', help='Release file')
        args = parser.parse_args(sys.argv[2:])

        if args.command == 'create':
            print('Create release')

        elif args.command == 'delete':
            print('Delete release')

        elif args.command == 'list':
            token = retrieve_token(token_file)
            list_releases(token)

        else:
            print('Unrecognized command')
            parser.print_help()
            exit(1)


if __name__ == '__main__':
    Github()
