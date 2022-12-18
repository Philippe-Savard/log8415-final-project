#!/bin/bash
# Run on all nodes
mkdir -p /opt/mysqlcluster/home
cd /opt/mysqlcluster/home
mkdir mysqlc
wget https://dev.mysql.com/get/Downloads/MySQL-Cluster-7.2/mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz
tar xvf mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz
mv /opt/mysqlcluster/home/mysql-cluster-gpl-7.2.1-linux2.6-x86_64/* mysqlc

#Run only on the managment node
mkdir -p /opt/mysqlcluster/deploy
cd /opt/mysqlcluster/deploy
mkdir conf
mkdir mysqld_data
mkdir ndb_data
cd conf
echo "[mysqld]" >> my.cnf
echo "ndbcluster" >> my.cnf
echo "datadir=/opt/mysqlcluster/deploy/mysqld_data">>my.cnf
echo "basedir=/opt/mysqlcluster/home/mysqlc" >> my.cnf
echo "port=3306" >> my.cnf