#!/bin/bash
set -x
status_file=/tmp/userdata_status
echo "RUNNING" > ${status_file}

HAYSTACK=/var/log/cloud-init.log
NEEDLE="backgrounded Resizing took"

echo "Waiting for background resizing to finish" > ${status_file}
while [ $(grep "$NEEDLE" $HAYSTACK -i --count) -eq "0" ]; do
    echo "Waiting for backgrouded Resizing to finish"
    sleep 5
done

# Make the stack user
useradd stack -d /home/stack -s /bin/bash -g sudo
mkdir -p /home/stack
chown -R stack /home/stack
chown stack /tmp/userdata_status
echo "# User rules for root" >> /etc/sudoers.d/90-stack-user
echo "stack ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/90-stack-user
chmod 440 /etc/sudoers.d/90-stack-user

echo "Installing software before devstack" > ${status_file}
# Required software
apt-get update
apt-get install -y git python-pip lvm2 vim squid3

echo "Creating logical volumes on ssds" > ${status_file}
# Init the ssd space on the baremetal io
pvcreate /dev/sdb
pvcreate /dev/sdc
vgcreate ssdpool /dev/sdb /dev/sdc
lvcreate -L 1024G -n ssd1 ssdpool
mkfs.ext4 /dev/mapper/ssdpool-ssd1
mount -t ext4 /dev/mapper/ssdpool-ssd1 /opt

# Drop in the correct neutron ml2 configs. Devtack does not currently support
# the needed sections for a working ml2 linuxbridge neutron with vxlan tenant networks.
# Therefore, we need to configure it ourselves

cat <<EOF >> /tmp/ml2_conf.ini
[ml2]
type_drivers = flat,vlan,vxlan,local
tenant_network_types = vxlan,flat
mechanism_drivers = linuxbridge,l2population


[ml2_type_flat]
flat_networks = vlan




[ml2_type_vxlan]
vxlan_group = 
vni_ranges = 1:1000


[vxlan]
enable_vxlan = True
vxlan_group = 
local_ip = $(ifconfig bond0.101 | awk '/inet addr/{print substr($2,6)}')
l2_population = True


[agent]
tunnel_types = vxlan
## VXLAN udp port
# This is set for the vxlan port and while this
# is being set here it's ignored because
# the port is assigned by the kernel
vxlan_udp_port = 4789


[linux_bridge]
physical_interface_mappings = vlan:bond0.101


[l2pop]
agent_boot_time = 180

[securitygroup]
enable_security_group = True
enable_ipset = True
firewall_driver = neutron.agent.linux.iptables_firewall.IptablesFirewallDriver
EOF

cat <<'EOF' >> /home/stack/init.sh
#!/bin/bash
touch /tmp/doesthisevenrun
set -x
{

    status_file=/tmp/userdata_status
    # Upgrade setuptools
    sudo pip install --upgrade setuptools
    sudo pip install --upgrade decorator

    # grant external access to vms
    echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward
    sudo iptables -t nat -A POSTROUTING -o bond0.101 -j MASQUERADE

    # Creating a sub-interface with an IP to use as a gateway
    # for the neutron physical provider network. 
    sudo ip addr add 172.16.1.2/24 dev bond0.101 label bond0.101:1

    cd /home/stack
    ssh-keygen -t rsa -N "" -f /home/stack/.ssh/id_rsa

    # Clone devstack and checkout specific version
    git clone https://github.com/openstack-dev/devstack.git
    cd devstack
    git remote update
    git checkout stable/juno

    # Write contents of local.conf file
    echo "[[local|localrc]]" >> local.conf
    echo "ADMIN_PASSWORD=secrete" >> local.conf
    echo "DATABASE_PASSWORD=\$ADMIN_PASSWORD" >> local.conf
    echo "RABBIT_PASSWORD=\$ADMIN_PASSWORD" >> local.conf
    echo "SERVICE_PASSWORD=\$ADMIN_PASSWORD" >> local.conf
    echo "SERVICE_TOKEN=c324b782-43a9-24c1-c2c4-d513c4041b42" >> local.conf
    echo "LOGFILE=\$DEST/logs/stack.sh.log" >> local.conf
    echo "disable_service n-net" >> local.conf
    echo "enable_service q-svc" >> local.conf
    echo "enable_service q-agt" >> local.conf
    echo "enable_service q-dhcp" >> local.conf
    echo "enable_service q-l3" >> local.conf
    echo "enable_service q-meta" >> local.conf
    echo "enable_service neutron" >> local.conf
    echo "enable_service ceilometer-acompute ceilometer-acentral ceilometer-anotification ceilometer-collector" >> local.conf
    echo "enable_service ceilometer-alarm-evaluator,ceilometer-alarm-notifier" >> local.conf
    echo "enable_service ceilometer-api" >> local.conf
    echo "HOST_IP=$(ifconfig bond0.101 | awk '/inet addr/{print substr($2,6)}')" >> local.conf
    echo "Q_PLUGIN=ml2" >> local.conf
    echo "Q_ML2_TENANT_NETWORK_TYPE=vxlan" >> local.conf
    echo "Q_AGENT=linuxbridge" >> local.conf
    echo "Q_ML2_PLUGIN_MECHANISM_DRIVERS=linuxbridge,l2population" >> local.conf

    # Run devstack's stack.sh script
    echo "Stacking devstack" > ${status_file}
    ./stack.sh

    #source openrc admin admin secrete
    export OS_USERNAME=admin
    export OS_TENANT_NAME=admin
    export OS_PASSWORD=secrete
    export OS_AUTH_URL=http://$(ifconfig bond0.101 | awk '/inet addr/{print substr($2,6)}'):5000/v2.0

    # Delete neutron resources that have been put in place by devstack
    neutron router-gateway-clear router1
    neutron router-interface-delete router1 private-subnet
    neutron router-delete router1
    neutron net-delete private
    neutron net-delete public

    #Drop in correct ml2_conf.ini
    sudo mv /tmp/ml2_conf.ini /etc/neutron/plugins/ml2/ml2_conf.ini

    #Restart neutron services
    #Killing the services and starting them back up
    for i in q-svc q-agt q-dhcp q-l3 q-meta q-metering; do
        screen -S stack -p $i -X stuff "^C"
        screen -S stack -p $i -X stuff "^[[A"
        screen -S stack -p $i -X stuff "\n"
    done

    #Give the services a few seconds to start..
    sleep 5

    #Build correct networks and routers.
    neutron net-create --provider:physical_network=vlan --provider:network_type=flat --shared --router:external external_net
    neutron subnet-create external_net 172.16.1.0/24 --name external_subnet --gateway=172.16.1.2 --allocation-pool start=172.16.1.5,end=172.16.1.252
    neutron net-create --provider:network_type=vxlan --shared testnet1
    neutron subnet-create testnet1 10.241.0.0/24 --name testsubnet1 --dns-nameservers list=true 8.8.8.8 4.2.2.2
    neutron router-create test-router
    neutron router-gateway-set test-router external_net

    # add keypair
    nova keypair-add heat-key --pub-key /home/stack/.ssh/id_rsa.pub

    # add ssh and ping to default security rules
    nova secgroup-add-rule default tcp 22 22 0.0.0.0/0
    nova secgroup-add-rule default icmp -1 -1 0.0.0.0/0
    glance image-create --name "Ubuntu 12.04 software config" --disk-format qcow2 --location http://ab031d5abac8641e820c-98e3b8a8801f7f6b990cf4f6480303c9.r33.cf1.rackcdn.com/ubuntu-softwate-config.qcow2 --is-public True --container-format bare
    echo "Finished!"
} 2>&1 >> /home/stack/init-log
echo "FINISHED" > ${status_file}
EOF

chmod uo+x /home/stack/init.sh
chown stack /home/stack/init.sh

echo "Scheduled devstack" > ${status_file}
su stack -c "/home/stack/init.sh"