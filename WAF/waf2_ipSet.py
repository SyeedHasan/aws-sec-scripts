import boto3

waf = boto3.client('wafv2', region_name='us-east-1')
response = waf.get_ip_set(
    Name='SampleIpSet',
    Scope='REGIONAL',
    Id='29107cdb-729c-4361-ac0d-a094ed275993'
)
ipSet = response["IPSet"]["Addresses"]
for ip in ipSet:
    print(ip)