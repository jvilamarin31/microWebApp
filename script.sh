#!/bin/bash

# Install MySQL
echo "Installing MySQL"

debconf-set-selections <<< 'mysql-server mysql-server/root_password password root'
debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password root'

sudo apt update
sudo apt install mysql-server -y
sudo systemctl start mysql.service

#Create and fill each microservice database
echo "Creating and filling databases"
sudo mysql -h localhost -u root -proot < /home/vagrant/microUsers/db/users_db.sql
sudo mysql -h localhost -u root -proot < /home/vagrant/microProducts/db/products_db.sql
sudo mysql -h localhost -u root -proot < /home/vagrant/microOrders/db/orders_db.sql

#Adding permissions to remote access
echo "Adding permissions to remote access"
sudo sed -i 's/127.0.0.1/0.0.0.0/g' /etc/mysql/mysql.conf.d/mysqld.cnf
sudo systemctl restart mysql.service

# Instal Python Flask and Flask-MySQLdb
sudo apt install python3-dev default-libmysqlclient-dev build-essential pkg-config mysql-client python3-pip -y
pip3 install Flask==2.3.3
pip3 install flask-cors
pip3 install Flask-MySQLdb
pip install Flask-SQLAlchemy
pip3 install requests
pip3 install python-dotenv
