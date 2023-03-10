from boto3 import Session

class EC2Instances:

    def __init__(self, image_id, key_name) -> None:
        self.session = Session(profile_name='default')
        self.client = self.session.client('ec2')
        self.ressource = self.session.resource('ec2')
        self.image_id = image_id
        self.instances = []
        self.key_pair = self.create_key_pair(key_name)
        self.pkey = self.key_pair['KeyMaterial']

        with open("demo_key.pem", 'w') as file:
            file.write(self.pkey)

    def create_key_pair(self, key_name):
        """
        Creates a key pair to securely connect to the AWS instances
        :param key_name: The name of the key pair
        :param ec2_resource: The ec2 resource which will create the key pair
        :return: The newly created key_pair
        """
        # Check if the key_name describes a key-pair
        key_pairs = self.client.describe_key_pairs(
            Filters=[
                {
                    'Name': 'key-name',
                    'Values': [
                        key_name,
                    ]
                },
            ],
        )

        if key_pairs['KeyPairs']:
            return key_pairs['KeyPairs'][0]

        return self.client.create_key_pair(KeyName=key_name)


    def create_instances(self, private_ip_address, tag, security_group_ids, user_data="", type="t2.micro"):
        """
        Creates a EC2 instance.
        :param private_ip_address: The private ip address of the instance
        :param tag: name of the instance to create
        :param security_group_ids: The id of the security group for this instance
        :param user_data: script to run on creation of the instance
        :param type: type of the EC2 instance (t2.micro by default)
        """
        new_instance = self.client.run_instances(
            ImageId=self.image_id,
            MinCount=1,
            MaxCount=1,
            InstanceType=type,
            KeyName=self.key_pair['KeyName'],
            UserData=user_data,
            SecurityGroupIds=security_group_ids,
            SubnetId='subnet-012b1459537c6e6dc',  # us-east1a
            PrivateIpAddress=private_ip_address,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': tag
                        },
                    ]
                },
            ]
        )
        # Add the instance to the instance list for later removal
        self.instances.extend(new_instance['Instances'])
        return self.instances


    def terminate_all(self):
        """
        This method terminates all of the instances created using this object
        """
        try:
            ids = []
            waiter = self.client.get_waiter('instance_terminated')
            for instance in self.instances:
                ids.append(instance['InstanceId'])
            self.client.terminate_instances(InstanceIds=ids)
            waiter.wait(InstanceIds=ids)
        except Exception as e:
            print("ERROR : Failed to terminate instances with {}".format(e))


    def delete_key_pair(self):
        """
        This method delete the key pair for all of the instances
        """
        self.client.delete_key_pair(KeyName=self.key_pair['KeyName'])
