import os
import yaml


CONFIG_FILE = "conf.yaml"


def get_yaml(data):
    """
    Attempts to load yaml from data.
    @param data - String containing yaml
    @return Dictionary|None
    """
    try:
        return yaml.load(data)
    except yaml.parser.Error:
        return None


def config_from_env(config, map_):
    """
    Updates config with environment variables described by map_
    @param config - Dictionary config to update
    @param map_ - Dictionary keyed by config key names whose values are the
        names of environment variables.
    """
    for key, name in map_.items():
        value = os.getenv(name)
        if value:
            config[key] = value


def config_from_args(config, map_, args):
    """
    Updates config with values from args provided by an argparser.
    @param config - Dictionary config to update
    @param map - Dictionary keyed by config key names whose values are the
        names of attributes of an argparser namespace object.
    @param args - Namespace object created by argparse
    """
    for key, name in map_.items():
        value = getattr(args, name)
        if value:
            config[key] = value


def validate_config(config, config_name, env_name, arg_name):
    """
    Checks to make sure a key of config_name exists in dictionary config
    with a non false truth evaluation of the value.

    @param config - Dictionary
    @param config_name - String
    @param env_name - String
    @param arg_name - Stringconfig

    """
    if not config.get(config_name):
        raise Exception(
            "Please set the %s in configuration file, "
            "environment as %s, "
            "or as an argument %s" % (config_name, env_name, arg_name)
        )


def get_config(args):
    """
    Loads config from a file.
    Updates the config with environment variables.
    Updates the config with values from an argparser
    """
    # Use file specified in environment for configuration or the default
    config_file = os.getenv('DS_CONFIG_FILE') or CONFIG_FILE

    # Use file specified in arguments or the above
    config_file = args.ds_config_file or config_file

    try:
        config = None
        with open(config_file, 'r') as f:
            contents = f.read()
        # Try yaml then json
        config = get_yaml(contents)
    except IOError:
        print "Unable to read from config file %s" % config_file

    # Init config in case file not present
    if not config:
        config = {}
    if not config.get('auth'):
        config['auth'] = {}

    # Config from environment
    config_from_env(config, {
        'name': 'DS_NAME',
        'flavor': 'DS_FLAVOR',
        'image': 'DS_IMAGE',
        'key_name': 'DS_KEY_NAME',
        'id_file': 'DS_ID_FILE',
        'userdata_file': 'DS_USERDATA_FILE'
    })
    config_from_env(config['auth'], {
        'username': 'DS_AUTH_USERNAME',
        'project_id': 'DS_AUTH_PROJECT_ID',
        'api_key': 'DS_AUTH_API_KEY',
        'auth_url': 'DS_AUTH_AUTH_URL',
        'region_name': 'DS_AUTH_REGION_NAME'
    })

    # Config from args
    config_from_args(config, {
        'name': 'ds_name',
        'flavor': 'ds_flavor',
        'image': 'ds_image',
        'key_name': 'ds_key_name',
        'id_file': 'ds_id_file',
        'userdata_file': 'ds_userdata_file'
    }, args)
    config_from_args(config['auth'], {
        'username': 'ds_auth_username',
        'project_id': 'ds_auth_project_id',
        'api_key': 'ds_auth_api_key',
        'auth_url': 'ds_auth_auth_url',
        'region_name': 'ds_auth_region_name'
    }, args)

    # Validate configuration
    validation_always_required = [
        {
            'config': config['auth'],
            'name': 'username',
            'env_name': 'DS_AUTH_USERNAME',
            'arg_name': '--ds-auth-username'
        },
        {
            'config': config['auth'],
            'name': 'project_id',
            'env_name': 'DS_AUTH_PROJECT_ID',
            'arg_name': '--ds-auth-project-id'
        },
        {
            'config': config['auth'],
            'name': 'api_key',
            'env_name': 'DS_AUTH_API_KEY',
            'arg_name': '--ds-auth-api-key'
        },
        {
            'config': config['auth'],
            'name': 'auth_url',
            'env_name': 'DS_AUTH_AUTH_URL',
            'arg_name': '--ds-auth-auth-url'
        },
        {
            'config': config['auth'],
            'name': 'region_name',
            'env_name': 'DS_AUTH_REGION_NAME',
            'arg_name': '--ds-auth-region-name'
        },
        {
            'config': config,
            'name': 'id_file',
            'env_name': 'DS_ID_FILE',
            'arg_name': '--ds-id-file'
        }
    ]

    for i in validation_always_required:
        validate_config(i['config'], i['name'],
                        i['env_name'], i['arg_name'])

    if args.action == 'create':
        validation_on_create = [
            {
                'config': config,
                'name': 'name',
                'env_name': 'DS_NAME',
                'arg_name': '--ds-name'
            },
            {
                'config': config,
                'name': 'flavor',
                'env_name': 'DS_FLAVOR',
                'arg_name': '--ds-flavor'
            },
            {
                'config': config,
                'name': 'image',
                'env_name': 'DS_IMAGE',
                'arg_name': '--ds-image'
            },
            {
                'config': config,
                'name': 'key_name',
                'env_name': 'DS_KEY_NAME',
                'arg_name': '--ds-key-name'
            },
            {
                'config': config,
                'name': 'userdata_file',
                'env_name': 'DS_USERDATA_FILE',
                'arg_name': '--ds-userdata-file'
            },
        ]
        for i in validation_on_create:
            validate_config(i['config'], i['name'],
                            i['env_name'], i['arg_name'])
    return config
