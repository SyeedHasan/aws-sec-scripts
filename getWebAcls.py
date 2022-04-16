#!/bin/python3

from os import name
from urllib import request
import boto3
import argparse
import os


def returnRuleId():
    pass

# Returns a single web ACL as per the selected ID
def returnWebAcl(waf, selectedAcl, allAcls):

    id = ""    

    # Searching ACLs by count
    # Risky; though lists are ordered, the count might lead to unexpected results
    for count, acl in enumerate(allAcls):
        if count == int(selectedAcl):
            id = acl['WebACLId']

    # Searching ACLs by name
    # Could lead to clashes in ACL names
    for acl in allAcls:
        if acl['Name'] == selectedAcl:
            print(f"WebACLId against the selected ACL number: {acl['WebACLId']}")
            id = acl['WebACLId']
            
    webAcl = waf.get_web_acl(WebACLId=id)
    print("")
    print("WebACL:")
    print("---")
    print(webAcl['WebACL'])


# Returns all web ACL IDs
def returnAllWebAcls(waf):
    webAcls = waf.list_web_acls()

    # Generic Variables
    allAcls = []

    print(f"")
    print(f"Available ACLs:")
    print(f"---")
    for count, acl in enumerate(webAcls['WebACLs']):
        
        allAcls.append(acl)
        print(f'''
            Count: {count}
            Name: {acl['Name']} 
            ID: {acl['WebACLId']})''')
    
    return allAcls

# Configures the WAF client
def configureBoto(wafType):
    # Limitations: The client only operates on the classic version of WAF (not v2)
    waf = boto3.client(wafType)
    return waf

# Arguments for the script
def parseArguments():    
    argParser = argparse.ArgumentParser()
    argParser.add_argument('--type', required=True, default='waf', choices=['waf', 'waf-regional'], help='Select the type of WAF (Classic, V2, Regional')
    argParser.add_argument('--region', required=False, default='', choices=['global', 'us-east-1'], help='Select the region to search for ACLs')

    wafInputs = argParser.add_argument_group('WAF-specific Data Objects [Optional]')
    wafInputs.add_argument('--web-acl-id', required=False, help='Input the WebACLId [Optional]')
    wafInputs.add_argument('--rule-id', required=False, help='Input the RuleId [Optional]')

    args = argParser.parse_args()
    return args

def main():    
    print("")
    print("AWS Helper Script: IP Blocker")
    
    args = parseArguments()
    wafClient = configureBoto(args.type)
    webAcls = returnAllWebAcls(wafClient)    

    selectedAcl = input("Select an ACL by entering its number (Count): ")
    webAcl = returnWebAcl(wafClient, selectedAcl, webAcls)


if __name__ == "__main__":
    main()
