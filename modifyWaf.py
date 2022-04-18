#!/bin/python3

#
#   Name: modifyWaf.py
#   Owner: Syed Hasan  
#   Version: 0.1
#

from time import sleep
import boto3
import argparse
import os
import sys
import time


def updateRule(waf, ruleId):
    res = waf.update_rule(
        RuleId=ruleId,
        ChangeToken=changeToken["ChangeToken"],
        Updates=[
            {
                "Action": "INSERT",
                "Predicate": {
                    "Negated": False,
                    "Type": "IPMatch",
                    "DataId": "192.11.11.11/32",
                },
            },
        ],
    )


def addIpToDynamo(ipAddress):
    
    dynamo = boto3.client('dynamodb')    
    return dynamo
    

def updateIpSet(waf, ipSetId, ipType, ipValue):

    changeToken = waf.get_change_token()

    # To avoid accidental blockage of an entire subnet
    if str(ipValue).endswith(("/16", "/8", "/24")):
        print(
            "[Caution] Do you really wish to proceed with blocking an entire subnet? Going to sleep for 5 seconds..."
        )
        time.sleep(5)
    elif str(ipValue).endswith("/32"):
        pass
    elif str(ipValue).find("/") > 0:
        print(
            "[Error] The script currently doesn't support addition of the specified CIDR range. Please consult with the owner of the script."
        )
        sys.exit(1)

    ipSet = waf.get_ip_set(IPSetId=ipSetId)
    ipSetName = ipSet["IPSet"]["Name"]

    response = waf.update_ip_set(
        IPSetId=ipSetId,
        ChangeToken=changeToken["ChangeToken"],
        Updates=[
            {
                "Action": "INSERT",
                "IPSetDescriptor": {"Type": ipType, "Value": ipValue},
            },
        ],
    )

    if int(response["ResponseMetadata"]["HTTPStatusCode"]) == 200:
        print(f"[+] Successfully added {ipValue} to {ipSetId} ({ipSetName})")
        return response["ResponseMetadata"]["HTTPStatusCode"]

# Returns a single web ACL as per the selected ID
def returnWebAcl(waf, selectedAcl, allAcls):

    id = ""

    # Searching ACLs by count
    # Risky; though lists are ordered, the count might lead to unexpected results
    for count, acl in enumerate(allAcls):
        if count == int(selectedAcl):
            id = acl["WebACLId"]

    # Searching ACLs by name
    # Could lead to clashes in ACL names
    for acl in allAcls:
        if acl["Name"] == selectedAcl:
            print(f"WebACLId against the selected ACL number: {acl['WebACLId']}")
            id = acl["WebACLId"]

    webAcl = waf.get_web_acl(WebACLId=id)
    print("")
    print("WebACL:")
    print("---")
    print(webAcl["WebACL"])

    return webAcl


# Returns all web ACL IDs
def returnAllWebAcls(waf):
    webAcls = waf.list_web_acls()

    # Generic Variables
    allAcls = []
    
    if len(webAcls["WebACLs"]) <= 0:
        print("[-] No ACLs found. Consider reconfiguring the script with the correct region/shift to global coverage.")
        sys.exit(1)
    
    print(f"")
    print(f"Available ACLs:")
    print(f"---")
    
    for count, acl in enumerate(webAcls["WebACLs"]):

        allAcls.append(acl)
        print(
            f"""
            Count: {count}
            Name: {acl['Name']} 
            ID: {acl['WebACLId']})"""
        )

    return allAcls


# Configures the WAF client
def configureBoto(wafType):
    # Limitations: The client only operates on the classic version of WAF (not v2)
    waf = boto3.client(wafType)
    return waf


# Arguments for the script
def parseArguments():
    argParser = argparse.ArgumentParser()
    
    #TODO: Add support for sub-parsers
    
    argParser.add_argument(
        "--type",
        required=True,
        default="waf",
        choices=["waf", "waf-regional"],
        help="Select the type of WAF (Classic, V2, Regional",
    )
    argParser.add_argument(
        "--region",
        required=False,
        default="",
        choices=["global", "us-east-1"],
        help="Select the region to search for ACLs",
    )

    # Add support for Sub-parsers
    # URL: https://stackoverflow.com/questions/41698895/using-argparse-to-accept-only-one-group-of-required-arguments
    wafInputs = argParser.add_argument_group("WAF-specific Data Objects [Optional]")
    wafInputs.add_argument(
        "--web-acl-id", required=False, help="Input the WebACLId [Optional]"
    )
    wafInputs.add_argument(
        "--rule-id", required=False, help="Input the RuleId [Optional]"
    )

    ipSet = argParser.add_argument_group("Update IP Set")
    ipSet.add_argument(
        "--ip-set-id", required=False, help="Input the IpSetId [Optional]"
    )
    ipSet.add_argument(
        "--ip-type",
        required=False,
        default="IPV4",
        choices=["IPV4", "IPV6"],
        help="Select the type of IP address",
    )
    ipSet.add_argument(
        "--ip-value",
        required=False,
        help="[Caution] The actual IP address to add to the IP Set",
    )
    ipSet.add_argument(
        "--add-dynamo",
        default="False",
        required=False,
        choices=["True", "False"],
        help="Add the IP value (provided to the IP-set in DynamoDb"
    )

    args = argParser.parse_args()
    return args


def main():
    print("")
    print("AWS Helper Script: IP Blocker")

    args = parseArguments()
    wafClient = configureBoto(args.type)

    if args.rule_id:
        updateRule(wafClient, args.rule_id)

    elif args.ip_set_id:
        if args.ip_type and args.ip_value:
            updateIpSet(wafClient, args.ip_set_id, args.ip_type, args.ip_value)
            if args.add_dynamo and args.add_dynamo == True:
                addIpToDynamo(args.ip_value)
        else:
            print(
                "[Error] Please provide the correct IP type and IP address to add to the specified IP set"
            )
    else:
        webAcls = returnAllWebAcls(wafClient)

        selectedAcl = input("Select an ACL by entering its number (Count): ")
        webAcl = returnWebAcl(wafClient, selectedAcl, webAcls)


if __name__ == "__main__":
    main()

"""
README:

Sample Commands:
-- Block the IP in the specified IP set:
python3 getWebAcls.py --type waf-regional --ip-set-id 4754c798-ea1d-4176-8ff2-c1427cd0e921  --ip-type IPV4 --ip-value 212.21.11.111/32



"""
