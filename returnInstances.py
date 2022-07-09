#!/bin/python3

#
#   Name: returnInstances.py
#   Owner: Syed Hasan
#   Description: Return instances behind an Application/Classic load balancer
#   Version: 0.1
#

from time import sleep
import boto3
import botocore
import argparse
from tabulate import tabulate
from pprint import pprint


def returnInstanceData(instanceIds):

    ec2Client = session.client('ec2')
    response = ec2Client.describe_instances(
        InstanceIds=instanceIds
    )

    instanceData = []

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instanceData.append([instance["InstanceId"], instance["ImageId"],
                                instance["PrivateIpAddress"], instance["PublicIpAddress"], instance["VpcId"]])

    if verbosity is True:
        pprint(response)
    else:
        print(tabulate(instanceData, headers=[
              'Instance ID', 'AMI ID', "Private IPv4", "Public IPv4", "VPC ID"]))

    return response

def returnTargetGroups(elbClient, lbArn):

    print(f"Finding Target Groups against ALB's ARN: {lbArn}")
    response = elbClient.describe_target_groups(
        LoadBalancerArn=lbArn
    )
    
    if verbosity is True:
        pprint("Target Group Data:")
        pprint(response)
    
    instanceTargetGroups = []
    instanceIds = []
    
    for record in response['TargetGroups']:
        if record['TargetType'] == "instance":
            instanceTargetGroups.append(record['TargetGroupArn'])

    for groupArn in instanceTargetGroups:
        print(f"Finding Instances against the Target Group ARN: {groupArn}")
        groupHealthResponse = elbClient.describe_target_health(
        TargetGroupArn=groupArn
    )
        
    for group in groupHealthResponse["TargetHealthDescriptions"]:
        instanceIds.append(group['Target']['Id'])
    
    print(f"Listing Instance Data for {len(instanceIds)} Instances:")
    returnInstanceData(instanceIds) 

def returnApplicationLbInfo(elbClient, elbName):
    print(f"Finding Load Balancers (Name): {elbName}")
    try:
        response = elbClient.describe_load_balancers(
            Names=[
                elbName
            ]
        )

    except elbClient.exceptions.AccessPointNotFoundException:
        print("No Load Balancer Found. Retry with the right filters?")
        return

    except Exception as e:
        print("Unknown Error... Quitting the script. Printing the Exception below:")
        print(e.message)
        return

    print(f"Found {len(response['LoadBalancers'])} Load Balancer")
    if verbosity is True:
        pprint(response)

    lbData = []

    for record in response["LoadBalancers"]:
        lbData.append([record['LoadBalancerArn'],
                      record['DNSName'], record['LoadBalancerName']])

    if verbosity is True:
        pprint(response)
    else:
        print(tabulate(lbData, headers=[
              'Load Balancer ARN', 'DNS Name', "Load Balancer Name"]))

    if len(lbData) > 1:
        lbArn = input("Select the LB ARN to retrieve the Target Groups:")
    else:
        lbArn = lbData[0][0]

    print()
    print("Discovering Attached Instances:")
    returnTargetGroups(elbClient, lbArn)

    return response


def returnClassicLbInfo(elbClient, elbName):

    print(f"Finding Load Balancers (Name): {elbName}")
    try:
        response = elbClient.describe_load_balancers(
            LoadBalancerNames=[
                elbName
            ]
        )
    except elbClient.exceptions.AccessPointNotFoundException:
        print("No Load Balancer Found. Retry with the right filters?")
        return
    except Exception as e:
        print("Unknown Error... Quitting the script. Printing the Exception below:")
        print(e.message)
        return

    print(f"Found {len(response['LoadBalancerDescriptions'])} Load Balancer")
    if verbosity is True:
        pprint(response)

    instanceIds = []

    for record in response["LoadBalancerDescriptions"]:
        for instance in record["Instances"]:
            instanceIds.append(instance["InstanceId"])

    print("Discovering Attached Instances:")
    returnInstanceData(instanceIds)

    return response


def configureBoto(service):

    global session
    session = boto3.Session(profile_name='temp')

    confService = session.client(service)
    return confService


def parseArguments():
    argParser = argparse.ArgumentParser()

    argParser.add_argument(
        "--client-type",
        required=False,
        default="elb",
        choices=["elb", "elbv2"],
        help="Select the type of ELB client (Boto3-specific setting",
    )

    argParser.add_argument(
        "--lb-type",
        required=True,
        default="classic",
        choices=["classic", "application"],
        help="Select the type of ELB",
    )

    argParser.add_argument(
        "--region",
        required=False,
        default="us-east-1",
        help="Select the region to search for ELBs",
    )

    argParser.add_argument(
        "--verbose",
        required=False,
        default="False",
        choices=["True", "False"],
        help="Should the outputs be displayed in a verbose mode?",
    )

    loadBalancerInputs = argParser.add_argument_group(
        "ELB-specific Data Objects [Optional]")
    loadBalancerInputs.add_argument(
        "--elb-name", required=False, help="Input the Load Balancer's Name [Optional]"
    )

    args = argParser.parse_args()
    return args


def main():
    print()
    print("Discover Load Balancers and Associated Instances")
    print("---")

    args = parseArguments()

    global verbosity
    verbosity = args.verbose

    if args.lb_type == "application":
        args.elb_type = "elbv2"
    else:
        args.elb_type = "elb"

    elbClient = configureBoto(args.client_type)
    if args.elb_type == "elb":
        returnClassicLbInfo(elbClient, args.elb_name)
    else:
        returnApplicationLbInfo(elbClient, args.elb_name)


if __name__ == "__main__":
    main()

"""
Using the AWS CLI:
    - aws elb describe-load-balancers --load-balancer-name my-classic-lb
    x {Find the ALB, Find the Target Group ARN}
    - aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:us-east-1:298189759279:targetgroup/my-tg-group/122653ca0900ca69  --query 'TargetHealthDescriptions[*].Target.Id'

Using the Script:
    - python .\returnInstances.py --client-type elbv2 --lb-type application --elb-name my-appp-load-balancer
    - python .\returnInstances.py --client-type elb --lb-type classic --elb-name my-classic-lb

"""
