import boto3

def lambda_handler(event=None, context=None):
    ec2 = boto3.client('ec2')
    iam = boto3.client('iam')
    cf = boto3.client('cloudformation')

    stack_name = 'mdso-stack'
    my_ip = '88.9.254.238/32'

    outputs = cf.describe_stacks(StackName=stack_name)['Stacks'][0]['Outputs']
    output_map = { o['OutputKey']: o['OutputValue'] for o in outputs }

    sg_id = output_map.get('SecurityGroupIds')
    role_name = output_map.get('RoleId')

    if not sg_id or not role_name:
        return { 'status': 'FAIL', 'reason': 'Missing stack outputs' }

    # Validate security group
    response = ec2.describe_security_groups(GroupIds=[sg_id])
    permissions = response['SecurityGroups'][0]['IpPermissions']
    for perm in permissions:
        if perm.get('FromPort') == 22 and perm.get('ToPort') == 22:
            for ip_range in perm['IpRanges']:
                if ip_range['CidrIp'] != my_ip:
                    print('Unexpected SSH access')
                    exit(1)

    # Validate IAM policy
    policies = iam.list_role_policies(RoleName=role_name)['PolicyNames']
    if 'S3ReadAccess' not in policies:
        print('S3 policy not found')
        exit(1)

    print('All tests passed')
