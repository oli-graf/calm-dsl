#!/bin/bash
set -ex
# -*- Install httpd and php
sudo setenforce 0
sudo sed -i 's/permissive/disabled/' /etc/sysconfig/selinux
sudo dnf update -y
sudo dnf -y install epel-release
sudo dnf config-manager --set-enabled crb
sudo dnf install dnf-utils http://rpms.remirepo.net/enterprise/remi-release-9.rpm -y
sudo rpm -Uvh https://mirror.webtatic.com/yum/el7/webtatic-release.rpm
sudo dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm https://dl.fedoraproject.org/pub/epel/epel-next-release-latest-9.noarch.rpm
#sudo yum -y install http://rpms.remirepo.net/enterprise/remi-release-9.1.rpm
sudo dnf module enable php:remi-8.1 -y
sudo dnf install -y httpd php php-mysqlnd.x86_64 php-fpm php-gd wget unzip


sudo systemctl enable httpd