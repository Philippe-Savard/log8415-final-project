from boto3 import Session


class SecurityGroup:

    def __init__(self, vpc_id, name="", description="default", ingress_rules=[], egress_rules=[]) -> None:
        self.session = Session(profile_name='default')
        self.client = self.session.client('ec2')
        self.security_group = self.__create_security_group(vpc_id, name, description)

        if len(ingress_rules) > 0:
            self.add_inbound_rules(ingress_rules)

        if len(egress_rules) > 0:
            self.add_outbound_rules(egress_rules)

    def __create_security_group(self, vpc_id, name="", description="default"):
        """
        This method creates the security group and adds the inbound and outbound rules necessary.

        :param ec2: The ec2 resource that we can get from boto3
        :return: {
                "IpPermissionsEgress": [
                    {
                        "IpProtocol": "-1",
                        "IpRanges": [
                            {
                                "CidrIp": "0.0.0.0/0"
                            }
                        ],
                        "UserIdGroupPairs": []
                    }
                ],
                "Description": "My security group"
                "IpPermissions": [],
                "GroupName": "my-sg",
                "VpcId": "vpc-1a2b3c4d",
                "OwnerId": "123456789012",
                "GroupId": "sg-903004f8"
            }
        """
        return self.client.create_security_group(
            Description=description,
            GroupName=name,
            VpcId=vpc_id
        )

    def add_inbound_rules(self, ip_rules):
        """
        The rules accepted from incoming traffic will correspond to SSH, HTTP and HTTPS
        :param security_group: The security group to which we want to add rules
        :return: nothing
        """
        self.client.authorize_security_group_ingress(
            GroupId=self.security_group['GroupId'],
            IpPermissions=ip_rules
        )

    def add_outbound_rules(self, ip_rules):
        """
        The rules accepted to go to the outside traffic will be HTTP and HTTPS
        AWS adds also a default all traffic rule
        :return: nothing
        """
        self.client.authorize_security_group_egress(
            GroupId=self.security_group['GroupId'],
            IpPermissions=ip_rules)

    def delete(self):
        """
        This function remove a security group
        :security_group_id : The security group to delete
        """
        try:
            self.client.delete_security_group(GroupId=self.security_group['GroupId'])
        except Exception as e:
            print("ERROR: failed to delete security group with GroupID={}. {}".format(self.security_group['GroupId'], e))
