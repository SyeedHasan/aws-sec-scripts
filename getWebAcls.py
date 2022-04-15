#!/bin/python3

from os import name
import boto3
import argparse
import os

print("AWS Helper Script: IP Blocker")

# Arguments for the script
argParser = argparse.ArgumentParser()
argParser.add_argument('--type', required=True, default='waf', choices=['waf', 'waf-regional'], help='Select the type of WAF (Classic, V2, Regional')
argParser.add_argument('--region', required=False, default='', choices=['global', 'us-east-1'], help='Select the region to search for ACLs')
args = argParser.parse_args()


# Limitations: The client only operates on the classic version of WAF (not v2)
waf = boto3.client(args.type)
webAcls = waf.list_web_acls()

# Generic Variables
allAcls = []
id = ""

print(f"")
print(f"Available ACLs in {args.type}")
print(f"---")
for count, acl in enumerate(webAcls['WebACLs']):
    
    allAcls.append(acl)
    
    print(f'''
        Count: {count}
        Name: {acl['Name']} 
        ID: {acl['WebACLId']})''')

print(f"")
selectedAcl = input("Select an ACL by entering its number (Count): ")

# Searching ACLs by count
# Risky; though lists are ordered, the count might lead to unexpected results
for count, acl in enumerate(allAcls):
    print(selectedAcl)
    if count == int(selectedAcl):
        print(acl)
        id = acl['WebACLId']

# Searching ACLs by name
# Could lead to clashes in ACL names
for acl in allAcls:
    if acl['Name'] == selectedAcl:
        print(f"WebACLId against the selected ACL: {acl['WebACLId']}")
        id = acl['WebACLId']
        
webAcl = waf.get_web_acl(WebACLId=id)
print("")
print("WebACL:")
print("---")
print(webAcl['WebACL'])

