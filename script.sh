#!/bin/bash

# Install MySQL
echo "Installing MySQL"
sudo apt update -y

debconf-set-selections <<< 'mysql-server mysql-server/root_password password root'
debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password root'

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

# Install Docker and Docker Compose
echo "Installing Docker and Docker Compose..."
sudo apt install ca-certificates curl gnupg -y

# Agregar la clave GPG oficial de Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Configurar el repositorio de Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker Engine, CLI, Containerd y Docker Compose
sudo apt update -y
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

# Habilitar e iniciar el servicio de Docker
sudo systemctl enable --now docker

# Permitir ejecutar Docker sin sudo para el usuario vagrant
sudo usermod -aG docker vagrant
