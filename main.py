import boto3
from instances import EC2Instances
from security_group import SecurityGroup

ip_addresses = {
    'ndb_mgmd': "172.31.0.4",
    'ndbd': ["172.31.0.5", "172.31.0.6", "172.31.0.7"]
}

if __name__ == "__main__":
    session = boto3.Session(profile_name='default')
    ec2_client = session.client('ec2')
    ec2_resource = session.resource('ec2')

    vpcs = ec2_client.describe_vpcs()
    vpc_id = vpcs.get('Vpcs', [{}])[0].get('VpcId', '')

    image_id = 'ami-08c40ec9ead489470'

    sg_mysql = SecurityGroup(vpc_id, name="mysql_group")

    mysqlc_nodes = EC2Instances(image_id, [sg_mysql.security_group['GroupId']], instance_type="t2.micro", key_name="vockey")

    try:
        # Create management node
        ndb_mgmd_data = ""
        with open('instances_config/ndb_mgmd_config.sh', 'r') as file:
            ndb_mgmd_data = file.read()

        ndb_mgmd_id = mysqlc_nodes.create_instances(ip_addresses["ndb_mgmd"], "ndb_mgmd", ndb_mgmd_data)[0]['InstanceId']
        print("ndb_mgmd node created with ID : {}".format(ndb_mgmd_id))

        # Create data nodes
        ndbd_data = ""
        with open('instances_config/ndbd_config.sh', 'r') as file:
            ndbd_data = file.read()

        for i, ip in enumerate(ip_addresses["ndbd"]):
            ndbd_id = mysqlc_nodes.create_instances(ip, "ndbd", ndbd_data)[1 + i]['InstanceId']
            print("ndbd_{} node created with ID : {}".format(1 + i, ndbd_id))

        waiter = ec2_client.get_waiter('instance_running')
        ids = []
        for instance in mysqlc_nodes.instances:
            ids.append(instance['InstanceId'])

        print("Waiting for all instances to be running")
        waiter.wait(InstanceIds=ids)

        input("Press ENTER to terminate all instances...")

    except Exception as e:
        print(e)
    finally:
        print("Removing instances...")
        mysqlc_nodes.terminate_all()
        # mysql_nodes.delete_key_pair()
        sg_mysql.delete()
