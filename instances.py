from boto3 import Session


class EC2Instances:

    def __init__(self, image_id, security_group_ids, instance_type, key_name) -> None:
        self.session = Session(profile_name='default')
        self.client = self.session.client('ec2')
        self.ressource = self.session.resource('ec2')
        self.image_id = image_id
        self.type = instance_type
        self.instances = []
        self.security_group_ids = security_group_ids
        self.key_pair = self.create_key_pair(key_name)

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

    def create_instances(self, private_ip_address, tag, user_data=""):
        self.instances.extend(
            self.client.run_instances(
                ImageId=self.image_id,
                MinCount=1,
                MaxCount=1,
                InstanceType=self.type,
                KeyName=self.key_pair['KeyName'],
                UserData=user_data,
                SecurityGroupIds=self.security_group_ids,
                SubnetId='subnet-0d6af2ce628f6f9e2',
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
        )
        return self.instances

    def terminate_all(self):
        for instance in self.instances:
            instance.terminate()
            instance.wait_until_terminated()

    def delete_key_pair(self):
        self.client.delete_key_pair(KeyName=self.key_pair['KeyName'])
