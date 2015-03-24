import argparse


def get_parser():
    version = 1.0
    desc = ("Manage an OpenStack vm with configured flavor, "
            "image, and userdata.")
    parser = argparse.ArgumentParser(description=desc)

    config_args = [
        (str, '--ds-config-file', 'Configuration file'),
        (str, '--ds-name', 'Server name'),
        (str, '--ds-flavor', 'Server flavor'),
        (str, '--ds-image', 'Server image'),
        (str, '--ds-key-name', 'Name of keypair for ssh access to server'),
        (str, '--ds-id-file', 'File to store id of server'),
        (str, '--ds-userdata-file', 'File to send as userdate to the server'),
        (str, '--ds-auth-username', 'Username of cloud account'),
        (str, '--ds-auth-project-id', 'Tenant id of account'),
        (str, '--ds-auth-api-key', 'Api key of account'),
        (str, '--ds-auth-auth-url', 'Auth url'),
        (str, '--ds-auth-region-name', 'Region name'),
        (str, '--ds-ssh-user', 'SSH user of created vm'),
        (
            int,
            '--ds-create-timeout',
            'Timeout in seconds for vm creation to complete'
        ),
        (
            int,
            '--ds-ssh-timeout',
            'Timeout in seconds when SSH\'ing into created vm'
        ),
        (
            str,
            '--ds-ssh-keyfile',
            'File containing private key to use with SSH'
        ),
        (
            str,
            '--ds-userdata-end-status',
            ('Userdata status file is expected to contain this value '
             'to signal complete.')
        ),
        (
            str,
            '--ds-userdata-status-file',
            'File expected to contain status of userdata script'
        )
    ]

    for type_, name, help_ in config_args:
        parser.add_argument(name, type=type_, help=help_)

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + str(version))

    parser.add_argument('action', choices=['create', 'delete'],
                        help="Create or Delete the server")

    help_ = (
        "Indicates that this tool should attempt to wait for userdata to "
        "complete before signalling success."
    )
    parser.add_argument('--wait-for-userdata',
                        help=help_, action='store_true', default=None)

    return parser
