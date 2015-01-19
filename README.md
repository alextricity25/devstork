#Devstork
Devstork is simple python tool used to create and delete a single OpenStack instance with configurable flavor, image, keypair, and a userdata script. When working with large, expensive public cloud vms, it can sometimes be useful to limit yourself to one instance in order to reduce cost. This tool attempts to create only one instance described by the configuration at a time and will not create another instance until the first one has been deleted.

### Userdata
The included script devstack-userdata.sh is designed for a public cloud OnMetal IO instance. devstack-userdata.sh creates the logical volumes on the ssds, installs devstack, adds ssh and icmp rules to the default security group, and imports a keypair.  This script is used to spin up a devstack instance with the intention of testing heat templates. This script can be changed to anything else and doesn't need to be devstack related.

### Example usage
Copy the sample-conf file and replace values with your values:
```shell
cp sample-conf conf
```

To create an instance:
```shell
python devstork.py --conf conf create
```

To delete an instance:
```shell
python devstork.py --conf conf delete
```
### Dependencies
[python-novaclient](https://github.com/openstack/python-novaclient)
