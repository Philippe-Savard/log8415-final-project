import boto3
from utils.instances import EC2Instances
from utils.security_group import SecurityGroup

# List of private ip addresses for EC2 instances
private_ip_addresses = {
    "proxy": "172.31.0.4",
    "ndb_mgmd": "172.31.0.5",
    "ndbd": ["172.31.0.6", "172.31.0.7", "172.31.0.8"],
    "standalone": "172.31.0.10"
}

session = boto3.Session(profile_name='default')
ec2_client = session.client('ec2')
ec2_resource = session.resource('ec2')

vpcs = ec2_client.describe_vpcs()
vpc_id = vpcs.get('Vpcs', [{}])[0].get('VpcId', '')

image_id = 'ami-08c40ec9ead489470'

ec2_instances = EC2Instances(image_id, key_name="demo_key")

public_ips = []

sg_mysql = None
sg_proxy = None
sg_standalone = None

try:
    sg_mysql = SecurityGroup(vpc_id, name="sql_cluster")

    #==========MANAGEMENT NODE CONFIG==========#
    ndb_mgmd_data = ""
    with open('config/ndb_mgmd_config.sh', 'r') as file:
        ndb_mgmd_data = file.read()

    ndb_mgmd_id = ec2_instances.create_instances(
        private_ip_addresses["ndb_mgmd"],
        "ndb_mgmd",
        [sg_mysql.security_group['GroupId']],
        ndb_mgmd_data
    )[0]['InstanceId']

    print("ndb_mgmd as been created with ID {}".format(ndb_mgmd_id))

    #=============DATA NODES CONFIG=============#
    ndbd_data = ""
    with open('config/ndbd_config.sh', 'r') as file:
        ndbd_data = file.read()

    ndbd_ids = []
    for i, private_ip in enumerate(private_ip_addresses["ndbd"]):
        id = ec2_instances.create_instances(
            private_ip,
            "ndbd_{}".format(1 + i),
            [sg_mysql.security_group['GroupId']],
            ndbd_data
        )[1 + i]['InstanceId']

        print("ndbd_{} as been created with ID {}".format(1 + i, id))
        ndbd_ids.append(id)

    print(ndbd_ids)
    waiter = ec2_client.get_waiter('instance_running')
    ids = []
    for instance in ec2_instances.instances:
        ids.append(instance['InstanceId'])

    print("Waiting on MySQL Nodes...")
    waiter.wait(InstanceIds=ids)

    public_ips.append("{}".format(ec2_resource.Instance(ndb_mgmd_id).public_ip_address))
    for i, id in enumerate(ndbd_ids):
        public_ips.append("{}".format(ec2_resource.Instance(id).public_ip_address))

    print(public_ips)
    #================PROXY CONFIG===============#

    sg_proxy = SecurityGroup(vpc_id, "proxy_security_group")

    proxy_data = ""
    with open('config/proxy_server_config.sh', 'r') as file:
        proxy_data = file.read()

    proxy_data += "\necho \"{}\" >> pkey.pem".format(ec2_instances.pkey)

    # Send the public ip addresses to the proxy server
    for ip in public_ips:
        proxy_data += "\necho \"{}\" >> /home/ubuntu/flaskapp/public_ips.txt".format(str(ip))

    # Create the proxy instance
    proxy_id = ec2_instances.create_instances(
        private_ip_addresses["proxy"],
        "proxy",
        [sg_proxy.security_group['GroupId']],
        proxy_data,
        "t2.large"
    )[4]['InstanceId']

    print("proxy node created with ID : {}".format(proxy_id))

    #=============STANDALONE CONFIG=============#
    sg_standalone = SecurityGroup(vpc_id, "standalone_group")

    standalone_data = ""
    with open('config/standalone_config.sh', 'r') as file:
        standalone_data = file.read()

    standalone_id = ec2_instances.create_instances(
        private_ip_addresses["standalone"],
        "standalone",
        [sg_standalone.security_group['GroupId']],
        standalone_data
    )[5]['InstanceId']

    print("standalone instance created with ID : {}".format(standalone_id))

    #==================TEARDOWN=================#

    waiter = ec2_client.get_waiter('instance_running')
    ids = []
    for instance in ec2_instances.instances:
        ids.append(instance['InstanceId'])

    print("Waiting on proxy server...")
    waiter.wait(InstanceIds=ids)

    input("Press ENTER to terminate all instances...")

except Exception as e:
    print("ERROR : failed to complete main {}".format(e))
finally:
    print("Removing instances...")
    ec2_instances.terminate_all()
    ec2_instances.delete_key_pair()
    print("Removing security groups...")
    if sg_mysql:
        sg_mysql.delete()

    if sg_proxy:
        sg_proxy.delete()

    if sg_standalone:
        sg_standalone.delete()
