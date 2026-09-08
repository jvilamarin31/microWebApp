# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.define :servidorWeb do |servidorWeb|
    servidorWeb.vm.box = "bento/ubuntu-22.04"
    servidorWeb.vm.network :private_network, ip: "192.168.56.3"
    servidorWeb.vm.network "forwarded_port", guest: 8080, host: 8080, auto_correct: true
    servidorWeb.vm.network "forwarded_port", guest: 8500, host: 8500, auto_correct: true
    servidorWeb.vm.provision "file", source: "frontend", destination: "/home/vagrant/frontend"
    servidorWeb.vm.provision "file", source: "microUsers", destination: "/home/vagrant/microUsers"
    servidorWeb.vm.provision "file", source: "microProducts", destination: "/home/vagrant/microProducts"
    servidorWeb.vm.provision "file", source: "microOrders", destination: "/home/vagrant/microOrders"
    servidorWeb.vm.provision "file", source: "docker-compose.yml", destination: "/home/vagrant/docker-compose.yml"
    servidorWeb.vm.provision "file", source: ".env.example", destination: "/home/vagrant/.env.example"
    servidorWeb.vm.provision "shell", path: "script.sh"
    servidorWeb.vm.hostname = "servidorWeb"
  end
end
