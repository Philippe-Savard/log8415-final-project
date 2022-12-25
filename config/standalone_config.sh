#!/bin/bash
# Download and extract the sakila sample db
cd ~
wget https://downloads.mysql.com/docs/sakila-db.tar.gz
tar xvf sakila-db.tar.gz

# Install mysql server on the instance
apt-get update
apt-get install mysql-server -y
apt-get install sysbench -y

mysql -u root -p -e "SOURCE ~/sakila-db/sakila-schema.sql; SOURCE ~/sakila-db/sakila-data.sql; USE sakila;"
mysql -u root -p -e "CREATE USER 'labuser'@'%' IDENTIFIED BY 'password'; GRANT ALL PRIVILEGES ON sakila.* TO 'labuser'@'%';"