from boto3 import Session


class SecurityGroup:

    def __init__(self, vpc_id, name="", ingress_rules=[], egress_rules=[]) -> None:
        """
        Constructor for a SecurityGroup object using the default AWS profile.
        @param vpc_id: Virtual private cloud identification string for the security group.
        @param name: name of the security group
        """
        self.session = Session(profile_name='default')
        self.client = self.session.client('ec2')
        self.security_group = self.client.create_security_group(
            Description="Security groupe for {}.".format(name), 
            GroupName=name,
            VpcId=vpc_id
        )
        
        if len(ingress_rules) == 0:
            ingress_rules.append(
                {
                    'IpProtocol': 'tcp', 
                    'FromPort': 0, 
                    'ToPort': 65535, # TCP/IP ports on IPv4 are bounded between 0 and 65535.
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            )

        self.client.authorize_security_group_ingress(
            GroupId=self.security_group['GroupId'],
            IpPermissions=ingress_rules
        )

        if len(egress_rules) == 0:
            egress_rules.append(
                {
                    'IpProtocol': 'tcp', 
                    'FromPort': 0, 
                    'ToPort': 65535, # TCP/IP ports on IPv4 are bounded between 0 and 65535.
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            )

        self.client.authorize_security_group_egress(
            GroupId=self.security_group['GroupId'],
            IpPermissions=egress_rules
        )

    def delete(self):
        """
        This function remove a security group
        :security_group_id : The security group to delete
        """
        try:
            self.client.delete_security_group(GroupId=self.security_group['GroupId'])
        except Exception as e:
            print("ERROR: failed to delete security group with GroupID={}. {}".format(self.security_group['GroupId'], e))
