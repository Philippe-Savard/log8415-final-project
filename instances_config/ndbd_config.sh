#!/bin/bash
# Based on the tutorial: Installing mysql cluster. https://stansantiago.wordpress.com/2012/ 
# Run on all nodes
mkdir -p /opt/mysqlcluster/home
cd /opt/mysqlcluster/home
mkdir mysqlc
wget https://dev.mysql.com/get/Downloads/MySQL-Cluster-7.2/mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz
tar xvf mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz
mv /opt/mysqlcluster/home/mysql-cluster-gpl-7.2.1-linux2.6-x86_64/* mysqlc
echo "export MYSQLC_HOME=/opt/mysqlcluster/home/mysqlc" > /etc/profile.d/mysqlc.sh
echo "export PATH=$MYSQLC_HOME/bin:$PATH" >> /etc/profile.d/mysqlc.sh
source /etc/profile.d/mysqlc.sh

#Run only on data nodes
mkdir -p /opt/mysqlcluster/deploy/ndb_data
ndbd -c ip-10-0-0-1.ec2.internal:1186