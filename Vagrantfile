# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.provider :libvirt do |libvirt|
    libvirt.driver = "kvm"
  end

  config.vm.define :servidorWeb do |servidorWeb|
    servidorWeb.vm.box = "generic/ubuntu2204"
    servidorWeb.vm.hostname = "servidorWeb"
    servidorWeb.vm.network :private_network, ip: "192.168.56.3"

    servidorWeb.vm.provision "file", source: "frontend", destination: "/home/vagrant/frontend"
    servidorWeb.vm.provision "file", source: "microUsers", destination: "/home/vagrant/microUsers"
    servidorWeb.vm.provision "file", source: "microProducts", destination: "/home/vagrant/microProducts"
    servidorWeb.vm.provision "file", source: "microOrders", destination: "/home/vagrant/microOrders"
    servidorWeb.vm.provision "shell", path: "script.sh"
  end
end
