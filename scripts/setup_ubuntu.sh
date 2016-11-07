#!/usr/bin/env bash
set -e



# Set up Docker APT source:

sudo apt-get update
sudo apt-get install -y \
  apt-transport-https \
  ca-certificates \

sudo apt-key adv \
  --keyserver 'hkp://p80.pool.sks-keyservers.net:80' \
  --recv-keys '58118E89F3A912897C070ADBF76221572C52609D' \

sudo tee /etc/apt/sources.list.d/docker.list \
  <<< "deb https://apt.dockerproject.org/repo ubuntu-$(lsb_release -cs) main"



# Install Docker, DNS server:

sudo apt-get update
sudo apt-get install -y \
  docker-engine \
  linux-image-extra-virtual \
  dnsmasq \

# python-ipaddress: see https://github.com/docker/compose/issues/3525
sudo apt-get install -y python-ipaddress || true

# Install Docker:
sudo adduser "${USER}" docker
sudo sh -c 'curl --retry 5 -L https://github.com/docker/compose/releases/download/1.8.0/run.sh > /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose'

# Set up local DNS server:
sudo tee /etc/dnsmasq.d/interfaces <<EOF
bind-interfaces
no-resolv
EOF

# Make local DNS server accept queries on the Docker network interface:
sudo tee /etc/dnsmasq.d/docker <<EOF
interface=docker0
EOF

# Use the Google public DNS servers as defaults:
sudo tee /etc/dnsmasq.d/google <<EOF
server=8.8.8.8
server=8.8.4.4
EOF

# Reload local DNS configuration:
sudo service dnsmasq restart

# Configure Docker daemon:
sudo tee /lib/systemd/system/docker.service <<EOF
[Unit]
Description=Docker Application Container Engine
Documentation=https://docs.docker.com
After=network.target docker.socket
Requires=docker.socket

[Service]
Type=notify
ExecStart=/usr/bin/docker daemon -H fd:// --bip=172.17.0.1/24 --dns=172.17.0.1
MountFlags=slave
LimitNOFILE=1048576
LimitNPROC=1048576
LimitCORE=infinity
TimeoutStartSec=0
# set delegate yes so that systemd does not reset the cgroups of docker containers
Delegate=yes

[Install]
WantedBy=multi-user.target
EOF

# Remove conflicting configuration in daemon.json if it exists:
sudo rm -f '/etc/docker/daemon.json'

# Reload Docker daemon configuration:
sudo systemctl daemon-reload
sudo service docker restart
