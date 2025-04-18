import yaml

def lambda_handler(event=None, context=None):
    with open('cloudformation-template.yaml', 'r') as file:
        template = yaml.safe_load(file)

    resources = template.get('Resources', {})

    # 1. Check Security Group SSH Rule
    sg = resources.get('EC2SecurityGroup', {})
    assert sg['Type'] == 'AWS::EC2::SecurityGroup', "EC2SecurityGroup type is incorrect"
    
    ingress = sg['Properties']['SecurityGroupIngress']
    assert any(
        rule['FromPort'] == 22 and
        rule['ToPort'] == 22 and
        rule['IpProtocol'] == 'tcp' and
        rule['CidrIp'] == '88.9.254.238/32'
        for rule in ingress
    ), "SSH access rule is incorrect"

    # 2. Check IAM Role for S3 Access
    role = resources.get('EC2InstanceRole', {})
    assert role['Type'] == 'AWS::IAM::Role', "EC2InstanceRole type is incorrect"

    policies = role['Properties'].get('Policies', [])
    s3_policy = next((p for p in policies if p['PolicyName'] == 'S3ReadAccess'), None)
    assert s3_policy, "S3ReadAccess policy not found"

    statements = s3_policy['PolicyDocument']['Statement']
    assert any(
        's3:ListBucket' in stmt['Action'] and
        stmt['Effect'] == 'Allow' and
        stmt['Resource'] == 'arn:aws:s3:::mdso-bucket'
        for stmt in statements
    ), "S3 policy is incorrect"

    print("✅ All template tests passed.")
    return { 'status': 'PASS' }

if __name__ == "__main__":
    lambda_handler()
