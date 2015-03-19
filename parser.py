import argparse


def get_parser():
    version = 1.0
    desc = ("Manage an OpenStack vm with configured flavor, "
            "image, and userdata.")
    parser = argparse.ArgumentParser(description=desc)

    config_args = [
        ('--ds-config-file', str, 'Configuration file'),
        ('--ds-name', str, 'Server name'),
        ('--ds-flavor', str, 'Server flavor'),
        ('--ds-image', str, 'Server image'),
        ('--ds-key-name', str, 'Name of keypair for ssh access to server'),
        ('--ds-id-file', str, 'File to store id of server'),
        ('--ds-userdata-file', str, 'File to send as userdate to the server'),
        ('--ds-auth-username', str, 'Username of cloud account'),
        ('--ds-auth-project-id', str, 'Tenant id of account'),
        ('--ds-auth-api-key', str, 'Api key of account'),
        ('--ds-auth-auth-url', str, 'Auth url'),
        ('--ds-auth-region-name', str, 'Region name')
    ]

    for name, type_, help_ in config_args:
        parser.add_argument(name, type=type_, help=help_)

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + str(version))

    parser.add_argument('action', choices=['create', 'delete'],
                        help="Create or Delete the server")
    return parser
