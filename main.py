import boto3
from instances import EC2Instances
from security_group import SecurityGroup

ip_addresses = {
    'ndb_mgmd': "10.0.0.1",
    'ndbd': ["10.0.0.2", "10.0.0.3", "10.0.0.4"]
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
        with open('ndb_mgmd_config.sh', 'r') as file:
            ndb_mgmd_data = file.read()

        mysqlc_nodes.create_instances(ip_addresses["ndb_mgmd"], "ndb_mgmd", ndb_mgmd_data)

        # Create data nodes
        ndbd_data = ""
        with open('ndbd_config.sh', 'r') as file:
            ndbd_data = file.read()

        for ip in ip_addresses["ndbd"]:
            mysqlc_nodes.create_instances(ip, "ndbd", ndbd_data)

        print("Waiting for all instances to be running")
        for instance in mysqlc_nodes.instances:
            id = instance.instance_id
            instance.wait_until_running()
            print("Instance {} as successfully been created and is running.".format(id))

        input("Press ENTER to terminate all instances...")

    except Exception as e:
        print(e)
    finally:
        print("Removing instances...")
        mysqlc_nodes.terminate_all()
        # mysql_nodes.delete_key_pair()
        sg_mysql.delete()
