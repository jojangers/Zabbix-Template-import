#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Owner: JTJ <jhtj@formula.fo>
# Version: 1.0

###########
# Imports #
###########
import os
import sys
import argparse
import glob
import json
from pathlib import Path

# pip install python-dotenv
try:
    from dotenv import dotenv_values
except ImportError:
    raise ImportError("you must install dotenv via pip install python-dotenv")

# pip install pyzabbix
try:
    from pyzabbix import ZabbixAPI, ZabbixAPIException
except ImportError:
    raise ImportError("you must install pyzabbix via pip install pyzabbix")



#####################
# Argument handling #
#####################

#initialise argument parser and add program name and description for help page
parser = argparse.ArgumentParser(prog = 'Zabbix template import',
                                 description = 'automatically imports zabbix temples with option to do it recursively.')


parser.add_argument('path', help='path to template in yaml format or root directory containing templates.')


# groups the api options into their own group
api_args = parser.add_argument_group(title='API options', description='options for connecting to the api. If api url is not defined, script will instead grab the variables from the ".env" file.')
# groups the import rules into their own group
rules_args = parser.add_argument_group(title='Import Rule options', description='options related to how the import should be handled if if already exists.')

api_args.add_argument('-a', '--api', 
                    help='zabbix api URL (if value is unset, connection variables will be imported from ".env" file', 
                    dest='api_url')

api_args.add_argument('-A', '--api-token', 
                      help='zabbix api token', 
                      dest='api_token')

api_args.add_argument('-u', '--username', 
                      help='zabbix api username',
                      dest='api_username')

api_args.add_argument('-p', '--password', 
                      help='zabbix api password', 
                      dest='api_password')

# rules related arguments
# TODO idea: somehow make it possible to override the selection on a rule by rule basis.
rules_args.add_argument('-D', '--delete-missing', 
                    help='Delete any values not present in imported templates', 
                    action='store_true', 
                    dest='delete_missing')

rules_args.add_argument('-E', '--no-update-existing', 
                    help='Update any already existing values', 
                    action='store_false', 
                    dest='update_existing')

rules_args.add_argument('-M', '--no-create-missing', 
                    help='Do not add any values not present in the current configuration', 
                    action='store_false', 
                    dest='create_missing')

# TODO: make this argument change the api function to "importcompare" and display the changes.
# current issues: have not been able to find a good way to format the importcompare response in a readable way.
parser.add_argument('-T', '--dry-run', 
                    help='display only list of templates to be imported', 
                    action='store_true', 
                    dest='dry_run')

parser.add_argument('-k', '--disable-ssl', 
                    help='disable ssl verification', 
                    action='store_false', 
                    dest='ssl_verify')

parser.add_argument('-r', '--recursive', 
                    help='search folder recursively', 
                    action='store_true',
                    dest='recurse')

'''
# TODO:
# 1: add validation for file
# 2: add example file for rules
# 3: overwrite default rules with rules in file (only overwrite rules defined in file, keep the rest as is)
parser.add_argument('-R', '--rules-file', 
                    help='overwrite import rules with rules found in file', 
                    dest='rules_file')
                    
# TODO: implement this (print the import rules then exit)
parser.add_argument('-#', '--display-rules',
                    help='display the import ruleset then exit')
'''

args = parser.parse_args()

# if both api token and password or username is supplied, exit with error.
if args.api_token and (args.api_password or args.api_username):
    parser.error('-A cannot be supplied with -u or -p')
    sys.exit(2)


# if api url is not defined from commandline
if not args.api_url:
    # load config from ".env" file into the config dictionary
    config = dotenv_values(".env")
    
    # if api token exists in env file and is not given through arguments, set the variable
    if config["ZBX_API_TOKEN"] and not args.api_token:
        ZABBIX_API = config["ZBX_API_TOKEN"] 
    # if api token is not defined exit with error
    elif not config["ZBX_API_TOKEN"] and not args.api_token:
        parser.error('please supply api token either via arguments or the ".env" file')
        sys.exit(2)
    
    # if api url exists, set variable
    if config["ZBX_API_URL"]:
        # if api token and server url variables exist in dictionary, overwrite the variables
        ZABBIX_SERVER = config["ZBX_API_URL"]
    # if api url is not defined exit with error
    elif not config["ZBX_API_URL"]:
        parser.error('please supply api url either via arguments or the ".env" file')
        sys.exit(2)
        
# if insecure requests are enabled:
if not args.ssl_verify:
    # import urllib3 to disable warnings on insecure requests.
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#############
# Variables #
#############

# TODO: add argument variables to correct variables

# configure rules for template import
# docs here: https://www.zabbix.com/documentation/current/en/manual/api/reference/configuration/import
rules = {
    "discoveryRules": {"createMissing": args.create_missing, "updateExisting": args.update_existing, "deleteMissing": args.delete_missing},
    "graphs": {"createMissing": args.create_missing, "updateExisting": args.update_existing, "deleteMissing": args.delete_missing},
    "host_groups": {"createMissing": args.create_missing, "updateExisting": args.update_existing},
    "template_groups": {"createMissing": args.create_missing, "updateExisting": args.update_existing},
    "hosts": {"createMissing": args.create_missing, "updateExisting": args.update_existing},
    "httptests": {"createMissing": args.create_missing, "updateExisting": args.update_existing, "deleteMissing": args.delete_missing},
    "images": {"createMissing": args.create_missing, "updateExisting": args.update_existing},
    "items": {"createMissing": args.create_missing, "updateExisting": args.update_existing, "deleteMissing": args.delete_missing},
    "maps": {"createMissing": args.create_missing, "updateExisting": args.update_existing},
    "mediaTypes": {"createMissing": args.create_missing, "updateExisting": args.update_existing},
    "templateLinkage": {"createMissing": args.create_missing, "deleteMissing": args.delete_missing},
    "templates": {"createMissing": args.create_missing, "updateExisting": args.update_existing},
    "templateDashboards": {"createMissing": args.create_missing, "updateExisting": args.update_existing, "deleteMissing": args.delete_missing},
    "triggers": {"createMissing": args.create_missing, "updateExisting": args.update_existing, "deleteMissing": args.delete_missing},
    "valueMaps": {"createMissing": args.create_missing, "updateExisting": args.update_existing, "deleteMissing": args.delete_missing},
}

ZABBIX_USERNAME = args.api_username
ZABBIX_PASSWORD = args.api_password

# initialise error list
error_list = []

################
# Initialising #
################


# create the zabbix api function
zapi = ZabbixAPI(ZABBIX_SERVER, detect_version=False)
# Disable SSL certificate verification
# zapi.session.verify = args.ssl_verify
zapi.session.verify = False

# if api token is defined, authenticate with api token
if ZABBIX_API:
    zapi.login(api_token=ZABBIX_API)
elif ZABBIX_USERNAME and ZABBIX_PASSWORD:
    zapi.login(ZABBIX_USERNAME, ZABBIX_PASSWORD)
else:
    parser.error('Missing api authentication variables.')
    sys.exit(2)

def zapi_import(filename):
    with open(filename, errors="ignore") as f:
        template = f.read()
        try:
            output = zapi.configuration['import'](format='yaml', source=template, rules=rules)
            print("result = " + str(output))
        except ZabbixAPIException as e:
            error_list += [filename + ": " + e]


##########
# Script #
##########



if os.path.isdir(args.path):
    
    # if recursion is enabled, use paths.rglob to recursively search directories
    if args.recurse:
        files = Path(args.path).rglob("*.yaml")
    elif not args.recurse:
        files = glob.glob(args.path + "\*.yaml")

    for file in files:
        # TODO: add some form of check to make multiple runs not go through the entire list of templates every time.
        print(file)
        if not args.dry_run:
            zapi_import(file)
            print("")

elif os.path.isfile(args.path):
    files = glob.glob(args.path)
    for file in files:
        print(file)
        if not args.dry_run:
            zapi_import(file)
else:
    # BUG: sometimes this will trigger if the given directory ends with a "\"
    print("I need a yaml file or directory.")

# print a list of the failed imports to ensure they dont get lost in the wall of text
for error in error_list:
    print(error)