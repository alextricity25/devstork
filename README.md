#Devstork
Devstork is simple python tool used to create and delete a single OpenStack instance with configurable flavor, image, keypair, and a userdata script. When working with large, expensive public cloud vms, it can sometimes be useful to limit yourself to one instance in order to reduce cost. This tool attempts to create only one instance described by the configuration at a time and will not create another instance until the first one has been deleted.

### Userdata
The included script devstack-userdata.sh is designed for a public cloud OnMetal IO instance. devstack-userdata.sh creates the logical volumes on the ssds, installs devstack, adds ssh and icmp rules to the default security group, and imports a keypair.  In addition, squid3 is installed to allow browsing of applications that use floating ips.  This script is used to spin up a devstack instance with the intention of testing heat templates. This script can be changed to anything else and doesn't need to be devstack related.

### Usage
```shell
python devstork.py --help
usage: devstork.py [-h] [--ds-config-file DS_CONFIG_FILE] [--ds-name DS_NAME]
                   [--ds-flavor DS_FLAVOR] [--ds-image DS_IMAGE]
                   [--ds-key-name DS_KEY_NAME] [--ds-id-file DS_ID_FILE]
                   [--ds-userdata-file DS_USERDATA_FILE]
                   [--ds-auth-username DS_AUTH_USERNAME]
                   [--ds-auth-project-id DS_AUTH_PROJECT_ID]
                   [--ds-auth-api-key DS_AUTH_API_KEY]
                   [--ds-auth-auth-url DS_AUTH_AUTH_URL]
                   [--ds-auth-region-name DS_AUTH_REGION_NAME] [--version]
                   {create,delete}

Manage an OpenStack vm with configured flavor, image, and userdata.

positional arguments:
  {create,delete}       Create or Delete the server

optional arguments:
  -h, --help            show this help message and exit
  --ds-config-file DS_CONFIG_FILE
                        Configuration file
  --ds-name DS_NAME     Server name
  --ds-flavor DS_FLAVOR
                        Server flavor
  --ds-image DS_IMAGE   Server image
  --ds-key-name DS_KEY_NAME
                        Name of keypair for ssh access to server
  --ds-id-file DS_ID_FILE
                        File to store id of server
  --ds-userdata-file DS_USERDATA_FILE
                        File to send as userdate to the server
  --ds-auth-username DS_AUTH_USERNAME
                        Username of cloud account
  --ds-auth-project-id DS_AUTH_PROJECT_ID
                        Tenant id of account
  --ds-auth-api-key DS_AUTH_API_KEY
                        Api key of account
  --ds-auth-auth-url DS_AUTH_AUTH_URL
                        Auth url
  --ds-auth-region-name DS_AUTH_REGION_NAME
                        Region name
  --version             show program's version number and exit
```

### Dependencies
[python-novaclient](https://github.com/openstack/python-novaclient)
