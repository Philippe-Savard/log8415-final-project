#!/bin/bash
# Based on the tutorial: Installing mysql cluster. https://stansantiago.wordpress.com/2012/ 
# Run on all nodes
service mysqld stop
yum remove mysql-server mysql mysql-devel

mkdir -p /opt/mysqlcluster/home
cd /opt/mysqlcluster/home
mkdir mysqlc
wget https://dev.mysql.com/get/Downloads/MySQL-Cluster-7.2/mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz
tar xvf mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz
mv /opt/mysqlcluster/home/mysql-cluster-gpl-7.2.1-linux2.6-x86_64/* mysqlc

echo "export MYSQLC_HOME=/opt/mysqlcluster/home/mysqlc" > /etc/profile.d/mysqlc.sh
echo "export PATH=$MYSQLC_HOME/bin:$PATH" >> /etc/profile.d/mysqlc.sh
source /etc/profile.d/mysqlc.sh

# EC2 instances are not initilized with this package
apt-get update
apt-get -y install libncurses5
apt-get install sysbench -y

#Run only on the managment/SQL node
mkdir -p /opt/mysqlcluster/deploy
cd /opt/mysqlcluster/deploy

mkdir conf
mkdir mysqld_data
mkdir ndb_data

cd conf
echo "[mysqld]" >> my.cnf
echo "ndbcluster" >> my.cnf
echo "datadir=/opt/mysqlcluster/deploy/mysqld_data" >> my.cnf
echo "basedir=/opt/mysqlcluster/home/mysqlc" >> my.cnf
echo "port=3306" >> my.cnf

echo "[ndb_mgmd]" >> config.ini
echo "hostname=ip-172-31-0-5.ec2.internal" >> config.ini
echo "datadir=/opt/mysqlcluster/deploy/ndb_data" >> config.ini
echo "nodeid=1" >> config.ini

# Data node default configuration
echo "[ndbd default]" >> config.ini
echo "noofreplicas=3" >> config.ini
echo "datadir=/opt/mysqlcluster/deploy/ndb_data" >> config.ini

# ndbd_1 : Data node 1
echo "[ndbd]" >> config.ini
echo "hostname=ip-172-31-0-6.ec2.internal" >> config.ini
echo "nodeid=2" >> config.ini

# ndbd_2 : Data node 2
echo "[ndbd]" >> config.ini
echo "hostname=ip-172-31-0-7.ec2.internal" >> config.ini
echo "nodeid=3" >> config.ini

# ndbd_3 : Data node 3
echo "[ndbd]" >> config.ini
echo "hostname=ip-172-31-0-8.ec2.internal" >> config.ini
echo "nodeid=4" >> config.ini

echo "[mysqld]" >> config.ini
echo "nodeid=50" >> config.ini

cd /opt/mysqlcluster/home/mysqlc

# Download sakila for testing
wget https://downloads.mysql.com/docs/sakila-db.tar.gz
tar xvf sakila-db.tar.gz

scripts/mysql_install_db --no-defaults --datadir=/opt/mysqlcluster/deploy/mysqld_data
bin/ndb_mgmd -f /opt/mysqlcluster/deploy/conf/config.ini --initial --configdir=/opt/mysqlcluster/deploy/conf
bin/mysqld --defaults-file=/opt/mysqlcluster/deploy/conf/my.cnf --user=root