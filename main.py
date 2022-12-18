import boto3
from instances import *
from security_group import *
from ssh_connection import *

if __name__ == "__main__":
    session = boto3.Session(profile_name='default')
    ec2_client = session.client('ec2')
    ec2_resource = session.resource('ec2')

    vpcs = ec2_client.describe_vpcs()
    vpc_id = vpcs.get('Vpcs', [{}])[0].get('VpcId', '')

    image_id = 'ami-08c40ec9ead489470'

    mysql_nodes = EC2Instances(image_id, instance_type="t2.micro", key_name="vockey")

    ip_in_rules = [
        {
            'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        },
        {
            'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        },
        {
            'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }
    ]

    ip_out_rules = [
        {
            'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        },
        {
            'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }
    ]

    sg_mysql = SecurityGroup(vpc_id, name="mysql_group", description="default", ingress_rules=ip_in_rules, egress_rules=ip_out_rules)

    instances = None

    try:
        user_data = ""
        with open('replica_config.sh', 'r') as file:
            user_data = file.read()

        instances = mysql_nodes.create_instances("mysql_slaves", 1, sg_mysql.security_group['GroupId'], user_data)
        print(instances)

        #instance = ec2_resource.Instance(instance.id)
        input("instance is ready, press a key to terminate...")
        # public_ip = instances.public_ip_address
        # print(public_ip)
        # TODO: Remove the file transfer since we will clone the git repository
        # folder_path = os.path.curdir
        # files = [
        #     os.path.join(folder_path, "install.sh"),
        #     os.path.join(folder_path, '4300.txt'),
        # ]
        ##start_deployment(public_ip, files, commands, key_pair["KeyMaterial"])

    except Exception as e:
        print(e)

    finally:
        mysql_nodes.terminate_all()
        # mysql_nodes.delete_key_pair()
        sg_mysql.delete()
