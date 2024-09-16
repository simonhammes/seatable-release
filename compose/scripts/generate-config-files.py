#!/usr/bin/env python3

import configparser
import json
import logging
import os
import sys

from typing import Dict

logger = logging.getLogger('generate-config-files')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

SERVER_PROTOCOL = os.getenv('SEATABLE_SERVER_PROTOCOL')
SERVER_HOSTNAME = os.getenv('SEATABLE_SERVER_HOSTNAME')
SERVER_URL = f'{SERVER_PROTOCOL}://{SERVER_HOSTNAME}'

CONFIG_DIR = '/opt/seatable/conf'

SEAFILE_CONF_PATH = os.path.join(CONFIG_DIR, 'seafile.conf')
CCNET_CONF_PATH = os.path.join(CONFIG_DIR, 'ccnet.conf')
DTABLE_WEB_CONF_PATH = os.path.join(CONFIG_DIR, 'dtable_web_settings.py')
DTABLE_WEB_OVERRIDES_CONF_PATH = os.path.join(CONFIG_DIR, 'dtable_web_settings_overrides.py')
SEATABLE_ROLES_PATH = os.path.join(CONFIG_DIR, 'seatable_roles.json')
GUNICORN_CONF_PATH = os.path.join(CONFIG_DIR, 'gunicorn.py')
DTABLE_SERVER_CONFIG_PATH = os.path.join(CONFIG_DIR, 'dtable_server_config.json')
DTABLE_DB_CONF_PATH = os.path.join(CONFIG_DIR, 'dtable-db.conf')
DTABLE_STORAGE_SERVER_CONF_PATH = os.path.join(CONFIG_DIR, 'dtable-storage-server.conf')
DTABLE_EVENTS_CONF_PATH = os.path.join(CONFIG_DIR, 'dtable-events.conf')
API_GATEWAY_CONF_PATH = os.path.join(CONFIG_DIR, 'dtable-api-gateway.conf')
NGINX_CONF_PATH = os.path.join(CONFIG_DIR, 'nginx.conf')

REQUIRED_VARIABLES = [
    'SEATABLE_SERVER_PROTOCOL',
    'SEATABLE_SERVER_HOSTNAME',
    'DB_HOST',
    'DB_ROOT_PASSWD',
    'DTABLE_WEB__SECRET_KEY',
    'DTABLE_WEB__DTABLE_PRIVATE_KEY',
]

# Specify default values
# Note: configparser only allows strings as values
# Note: Uppercase/lowercase matters here
DEFAULT_VALUES = {
    'SEAFILE__fileserver__port': '8082',
    # TODO: Enable Go fileserver by default?
    # 'SEAFILE__fileserver__use_go_fileserver': 'true',
    'SEAFILE__database__type': 'mysql',
    'SEAFILE__database__host': os.environ.get('DB_HOST'),
    'SEAFILE__database__port': '3306',
    'SEAFILE__database__user': os.environ.get('DB_USER', 'root'),
    'SEAFILE__database__password': os.environ.get('DB_ROOT_PASSWD'),
    'SEAFILE__database__db_name': 'seafile_db',
    'SEAFILE__database__connection_charset': 'utf8',
    'SEAFILE__history__keep_days': '60',

    'CCNET__Database__ENGINE': 'mysql',
    'CCNET__Database__HOST': os.environ.get('DB_HOST'),
    'CCNET__Database__PORT': '3306',
    'CCNET__Database__USER': os.environ.get('DB_USER', 'root'),
    'CCNET__Database__PASSWD': os.environ.get('DB_ROOT_PASSWD'),
    'CCNET__Database__DB': 'ccnet_db',
    'CCNET__Database__CONNECTION_CHARSET': 'utf8',

    'DTABLE_WEB__IS_PRO_VERSION': 'true',
    'DTABLE_WEB__COMPRESS_CACHE_BACKEND': 'locmem',
    # SECRET_KEY + DTABLE_PRIVATE_KEY are specified using environment variables
    'DTABLE_WEB__DTABLE_SERVER_URL': f'{SERVER_URL}/dtable-server/',
    'DTABLE_WEB__DTABLE_SOCKET_URL': f'{SERVER_URL}/',
    'DTABLE_WEB__DTABLE_WEB_SERVICE_URL': f'{SERVER_URL}/',
    'DTABLE_WEB__DTABLE_DB_URL': f'{SERVER_URL}/dtable-db/',
    'DTABLE_WEB__DTABLE_STORAGE_SERVER_URL': 'http://127.0.0.1:6666/',
    'DTABLE_WEB__NEW_DTABLE_IN_STORAGE_SERVER': 'true',
    'DTABLE_WEB__FILE_SERVER_ROOT': f'{SERVER_URL}/seafhttp/',
    'DTABLE_WEB__ENABLE_USER_TO_SET_NUMBER_SEPARATOR': 'true',
    'DTABLE_WEB__TIME_ZONE': os.environ.get('TIME_ZONE', 'UTC'),
    'DTABLE_WEB__DISABLE_ADDRESSBOOK_V1': 'true',
    'DTABLE_WEB__ENABLE_ADDRESSBOOK_V2': 'true',

    'DTABLE_SERVER__host': os.environ.get('DB_HOST'),
    'DTABLE_SERVER__user': os.environ.get('DB_USER', 'root'),
    'DTABLE_SERVER__password': os.environ.get('DB_ROOT_PASSWD'),
    'DTABLE_SERVER__database': 'dtable_db',
    'DTABLE_SERVER__port': '3306',
    # TODO: Find a better name for this shared secret
    'DTABLE_SERVER__private_key': os.environ.get('DTABLE_WEB__DTABLE_PRIVATE_KEY'),
    'DTABLE_SERVER__redis_host': 'redis',
    'DTABLE_SERVER__redis_port': '6379',
    'DTABLE_SERVER__redis_password': '',

    'DTABLE_DB__general__host': '127.0.0.1',
    'DTABLE_DB__general__port': '7777',
    'DTABLE_DB__general__log_dir': '/opt/seatable/logs',
    'DTABLE_DB__storage__data_dir': '/opt/seatable/db-data',
    'DTABLE_DB__dtable0x20cache__dtable_server_url': 'http://127.0.0.1:5000',
    'DTABLE_DB__backup__dtable_storage_server_url': 'http://127.0.0.1:6666',
    'DTABLE_DB__backup__keep_backup_num': '3',

    # Spaces in section names are encoded with '0x20' (HEX representation of a space character)
    # This is inspired by Gitea, which uses 0x2E for a dot character
    'DTABLE_STORAGE_SERVER__general__log_dir': '/opt/seatable/logs',
    'DTABLE_STORAGE_SERVER__general__temp_file_dir': '/tmp/tmp-storage-data',
    'DTABLE_STORAGE_SERVER__storage0x20backend__type': 'filesystem',
    'DTABLE_STORAGE_SERVER__storage0x20backend__path': '/opt/seatable/storage-data',
    'DTABLE_STORAGE_SERVER__snapshot__interval': '86400',
    'DTABLE_STORAGE_SERVER__snapshot__keep_days': '180',

    'DTABLE_EVENTS__DATABASE__type': 'mysql',
    'DTABLE_EVENTS__DATABASE__host': os.environ.get('DB_HOST'),
    'DTABLE_EVENTS__DATABASE__port': '3306',
    'DTABLE_EVENTS__DATABASE__username': os.environ.get('DB_USER', 'root'),
    'DTABLE_EVENTS__DATABASE__password': os.environ.get('DB_ROOT_PASSWD'),
    'DTABLE_EVENTS__DATABASE__db_name': 'dtable_db',
    'DTABLE_EVENTS__REDIS__host': 'redis',
    'DTABLE_EVENTS__REDIS__port': '6379',

    'API_GATEWAY__general__log_dir': '/opt/seatable/logs',
    'API_GATEWAY__general__host': '127.0.0.1',
    'API_GATEWAY__general__port': '7780',
    'API_GATEWAY__dtable-db__cluster_mode': 'false',
    'API_GATEWAY__dtable-db__server_address': 'http://127.0.0.1:7777',
    'API_GATEWAY__dtable-server__cluster_mode': 'false',
    'API_GATEWAY__dtable-server__server_address': 'http://127.0.0.1:5000',
}

# Generates a config file
# path is the file location
# prefix is the prefix for environment variables
def generate_conf_file(path: str, prefix: str):
    # Get all matching variables from "DEFAULT_VALUES"
    variables = {key: value for key, value in DEFAULT_VALUES.items() if key.startswith(prefix)}

    # Get matching environment variables
    user_variables = {key: value for key, value in os.environ.items() if key.startswith(prefix)}

    # Update variables, values supplied by the user take precedence
    variables.update(user_variables)

    config = configparser.ConfigParser()

    # Make ConfigParser case sensitive
    # Otherwise it lowercases keys before writing them to a file, but ccnet requires them to be in uppercase (e.g. 'HOST')
    config.optionxform = str

    for key, value in variables.items():
        parts = key.split('__')

        if len(parts) != 3:
            logger.error('Error: Variable "%s" does not match PREFIX__SECTION__KEY format', key)
            sys.exit(1)

        # Spaces in section names are encoded with '0x20' (HEX representation of a space character)
        # This is inspired by Gitea, which uses 0x2E for a dot character
        section = parts[1].replace('0x20', ' ')
        key = parts[2]

        if section not in config:
            # section does not exist yet
            config[section] = {}

        config[section][key] = value

    if not os.path.exists(path):
        logger.info(f'Generating {os.path.basename(path)} since it does not exist yet')
    else:
        logger.info(f'Updating {os.path.basename(path)}')

    with open(path, 'w') as file:
        config.write(file)

def generate_gunicorn_config_file(path: str):
    config_template = """
daemon = True
workers = 5
threads = 5

# default localhost:8000
bind = "127.0.0.1:8000"

# Pid
pidfile = '/opt/seatable/pids/dtable-web.pid'

# for file upload, we need a longer timeout value (default is only 30s, too short)
timeout = 1200

limit_request_line = 8190

enable_stdio_inheritance = %(enable_stdio_inheritance)s
"""

    config = {
        # Must be enabled if logs should go to stdout
        'enable_stdio_inheritance': os.environ.get('SEATABLE_LOG_TO_STDOUT', 'false').lower() == 'true'
    }

    if not os.path.exists(path):
        logger.info(f'Generating {os.path.basename(path)} since it does not exist yet')
    else:
        logger.info(f'Updating {os.path.basename(path)}')

    with open(path, 'w') as file:
        # Use lstrip() to remove leading whitespace
        file.write(config_template.lstrip() % config)

def generate_dtable_server_config_file(path: str):
    config = {}

    # Prefix for environment variables
    prefix = 'DTABLE_SERVER__'

    # Get all matching variables from "DEFAULT_VALUES"
    variables = {key: value for key, value in DEFAULT_VALUES.items() if key.startswith(prefix)}

    # Get matching environment variables
    user_variables = {key: value for key, value in os.environ.items() if key.startswith(prefix)}

    # Update variables, values supplied by the user take precedence
    variables.update(user_variables)

    for key, value in variables.items():
        parts = key.split('__')

        if len(parts) != 2:
            logger.error('Error: Variable "%s" does not match PREFIX__KEY format', key)
            sys.exit(1)

        key = parts[1]

        # Determine variable type
        if value.lower() in ['true', 'false']:
            # Boolean
            config[key] = value.lower() == "true"
        elif value.isdigit():
            # Number
            config[key] = int(value)
        else:
            # String
            config[key] = value

    if not os.path.exists(path):
        logger.info(f'Generating {os.path.basename(path)} since it does not exist yet')
    else:
        logger.info(f'Updating {os.path.basename(path)}')

    with open(path, 'w') as file:
        json.dump(config, file, indent=4)
        file.write('\n')

def generate_dtable_web_settings_file(path: str):
    database_config_template = """
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '%(host)s',
        'PORT': '%(port)s',
        'USER': '%(username)s',
        'PASSWORD': '%(password)s',
        'NAME': 'dtable_db',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}
"""

    database_config = {
        'host': os.environ['DB_HOST'],
        'port': '3306',
        'username': os.environ.get('DB_USER', 'root'),
        'password': os.environ['DB_ROOT_PASSWD'],
    }

    cache_config_template = """
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://%(host)s:%(port)s',
    },
    'locmem': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
}
"""

    cache_config = {
        'host': os.environ.get('DTABLE_WEB__CACHE_HOST', 'redis'),
        'port': os.environ.get('DTABLE_WEB__CACHE_PORT', '6379'),
    }

    # Generate lines for all the other settings
    lines = []

    # Prefix for environment variables
    prefix = 'DTABLE_WEB__'

    # Get all matching variables from "DEFAULT_VALUES"
    variables: dict[str, str] = {key: value for key, value in DEFAULT_VALUES.items() if key.startswith(prefix)}

    # Get matching environment variables
    user_variables = {key: value for key, value in os.environ.items() if key.startswith(prefix)}

    # Update variables, values supplied by the user take precedence
    variables.update(user_variables)

    # These variables are handled separately and should not cause auto-generated variable definitions
    excluded_variables = [
        'DTABLE_WEB__CACHE_BACKEND',
        'DTABLE_WEB__CACHE_HOST',
        'DTABLE_WEB__CACHE_PORT',
    ]

    # Exclude variables that are lists/tuples/dictionaries (for now)
    unsupported_variables = [
        'DTABLE_WEB__API_THROTTLE_RATES'
        'DTABLE_WEB__CUSTOM_COLORS'
        'DTABLE_WEB__LANGUAGES',
        'DTABLE_WEB__REST_FRAMEWORK_THROTTING_WHITELIST',
    ]

    for key, value in variables.items():
        if key in excluded_variables:
            continue
        elif key.startswith('DTABLE_WEB__SAML_ATTRIBUTE_MAP') or key.startswith('DTABLE_WEB__OAUTH_ATTRIBUTE_MAP'):
            # Ignore variables for OAuth/SAML attribute map configuration, these are handled separately
            continue
        elif key in unsupported_variables:
            logger.error('Error: Variable "%s" is currently not supported', key)
            sys.exit(1)

        parts = key.split('__')

        if len(parts) != 2:
            logger.error('Error: Variable "%s" does not match PREFIX__KEY format', key)
            sys.exit(1)

        key = parts[1]

        # TODO: Check if key exists in dtable-web/seahub/settings.py to prevent errors due to typos

        if key in ['OFFICE_WEB_APP_FILE_EXTENSION', 'OFFICE_WEB_APP_EDIT_FILE_EXTENSION', 'ONLYOFFICE_FILE_EXTENSION', 'ONLYOFFICE_EDIT_FILE_EXTENSION']:
            # Convert OnlyOffice/Collabora file extension variables from CSV to tuples
            lines.append(f'{key} = {repr(tuple(value.split(",")))}')
            continue
        elif key == 'OAUTH_SCOPE':
            # Convert OAUTH_SCOPE from CSV to list
            lines.append(f'{key} = {repr(value.split(","))}')
            continue

        # Determine variable type
        if value.lower() in ['true', 'false']:
            # Boolean
            lines.append(f'{key} = {value.lower() == "true"}')
        elif value.isdigit():
            # Number
            lines.append(f'{key} = {value}')
        else:
            # String
            lines.append(f'{key} = "{value}"')

    if not os.path.exists(path):
        logger.info(f'Generating {os.path.basename(path)} since it does not exist yet')
    else:
        logger.info(f'Updating {os.path.basename(path)}')

    with open(path, 'w') as file:
        file.write(database_config_template.lstrip() % database_config)
        file.write(cache_config_template % cache_config)
        file.write('\n')

        oauth_attribute_map = generate_oauth_attribute_map()
        if len(oauth_attribute_map) > 0:
            file.write(f'OAUTH_ATTRIBUTE_MAP = {repr(oauth_attribute_map)}\n')

        saml_attribute_map = generate_saml_attribute_map()
        if len(saml_attribute_map) > 0:
            file.write(f'SAML_ATTRIBUTE_MAP = {repr(saml_attribute_map)}\n')

        for line in lines:
            file.write(line)
            file.write('\n')

        # Roles can be specified using a JSON file
        if os.path.exists(SEATABLE_ROLES_PATH):
            logger.info('Loading user role definitions from %s into %s...', os.path.basename(SEATABLE_ROLES_PATH), os.path.basename(DTABLE_WEB_CONF_PATH))
            with open (SEATABLE_ROLES_PATH, "r") as roles_file:
                try:
                    contents = json.load(roles_file)
                except Exception as e:
                    logger.error('Failed to load %s due to %s: %s', os.path.basename(SEATABLE_ROLES_PATH), type(e).__name__, str(e))
                    sys.exit(1)

                file.writelines([
                    f'\n# Role definitions imported from {os.path.basename(SEATABLE_ROLES_PATH)}:\n',
                    f'ENABLED_ROLE_PERMISSIONS = {repr(contents)}\n',
                ])

        # Allow loading overrides file
        if os.path.exists(DTABLE_WEB_OVERRIDES_CONF_PATH):
            logger.info('Writing overrides from %s into %s...', os.path.basename(DTABLE_WEB_OVERRIDES_CONF_PATH), os.path.basename(DTABLE_WEB_CONF_PATH))
            with open (DTABLE_WEB_OVERRIDES_CONF_PATH, "r") as overrides:
                file.writelines([
                    f'\n# Overrides imported from {os.path.basename(DTABLE_WEB_OVERRIDES_CONF_PATH)}:\n',
                    overrides.read(),
                ])

def generate_oauth_attribute_map() -> Dict[str, str]:
    attribute_map = {}

    # Taken from seahub/oauth/views.py
    supported_attributes = ['uid', 'name', 'contact_email', 'user_role', 'employee_id']

    # attribute is the "SeaTable key", value is the key from the OAuth provider
    for attribute in supported_attributes:
        if value := os.environ.get(f'DTABLE_WEB__OAUTH_ATTRIBUTE_MAP__{attribute}'):
            attribute_map[value] = attribute

    return attribute_map

def generate_saml_attribute_map() -> Dict[str, str]:
    attribute_map = {}

    # Taken from seahub/saml/views.py
    supported_attributes = ['uid', 'name', 'contact_email', 'user_role', 'employee_id']

    # attribute is the "SeaTable key", value is the key from the SAML provider
    for attribute in supported_attributes:
        if value := os.environ.get(f'DTABLE_WEB__SAML_ATTRIBUTE_MAP__{attribute}'):
            attribute_map[value] = attribute

    return attribute_map

def generate_nginx_conf_file(path: str):
    config_template = """
log_format seatableformat '[$time_iso8601] $http_x_forwarded_for $remote_addr "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" $upstream_response_time';

upstream dtable_servers {
    server 127.0.0.1:5000;
    keepalive 15;
}

server {
    server_name %(server_name)s;
    listen 80;
    listen [::]:80;

    proxy_set_header X-Forwarded-For $remote_addr;

    location / {
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods GET,POST,PUT,DELETE,OPTIONS;
        add_header Access-Control-Allow-Headers "deviceType,token, authorization, content-type";
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods GET,POST,PUT,DELETE,OPTIONS;
            add_header Access-Control-Allow-Headers "deviceType,token, authorization, content-type";
            return 204;
        }
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $http_host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Host $server_name;
        proxy_read_timeout  1200s;

        # used for view/edit office file via Office Online Server
        client_max_body_size 0;

        access_log      /opt/nginx-logs/dtable-web.access.log seatableformat;
        error_log       /opt/nginx-logs/dtable-web.error.log;
    }

    location /seafhttp {
        rewrite ^/seafhttp(.*)$ $1 break;
        proxy_pass http://127.0.0.1:8082;

        client_max_body_size 0;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;

        proxy_request_buffering off;
        proxy_connect_timeout  36000s;
        proxy_read_timeout  36000s;
        proxy_send_timeout  36000s;

        send_timeout  36000s;

        access_log      /opt/nginx-logs/seafhttp.access.log seatableformat;
        error_log       /opt/nginx-logs/seafhttp.error.log;

    }

    location /media {
        root /opt/seatable/seatable-server-latest/dtable-web;
    }

    location /socket.io {
        proxy_pass http://dtable_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_redirect off;

        proxy_buffers 8 32k;
        proxy_buffer_size 64k;

        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_set_header X-NginX-Proxy true;

        access_log      /opt/nginx-logs/socket-io.access.log seatableformat;
        error_log       /opt/nginx-logs/socket-io.error.log;

    }

    location /dtable-server {
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods GET,POST,PUT,DELETE,OPTIONS;
        add_header Access-Control-Allow-Headers "deviceType,token, authorization, content-type";
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods GET,POST,PUT,DELETE,OPTIONS;
            add_header Access-Control-Allow-Headers "deviceType,token, authorization, content-type";
            return 204;
        }
        rewrite ^/dtable-server/(.*)$ /$1 break;
        proxy_pass         http://dtable_servers;
        proxy_redirect     off;
        proxy_set_header   Host              $http_host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Host  $server_name;
        proxy_set_header   X-Forwarded-Proto $scheme;

        # used for import excel
        client_max_body_size 100m;

        access_log      /opt/nginx-logs/dtable-server.access.log seatableformat;
        error_log       /opt/nginx-logs/dtable-server.error.log;

    }

    location /dtable-db/ {
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods GET,POST,PUT,DELETE,OPTIONS;
        add_header Access-Control-Allow-Headers "deviceType,token, authorization, content-type";
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods GET,POST,PUT,DELETE,OPTIONS;
            add_header Access-Control-Allow-Headers "deviceType,token, authorization, content-type";
            return 204;
        }
        proxy_pass         http://127.0.0.1:7777/;
        proxy_redirect     off;
        proxy_set_header   Host              $http_host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Host  $server_name;
        proxy_set_header   X-Forwarded-Proto $scheme;

        access_log      /opt/nginx-logs/dtable-db.access.log seatableformat;
        error_log       /opt/nginx-logs/dtable-db.error.log;
    }

    location /api-gateway/ {
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods GET,POST,PUT,DELETE,OPTIONS;
        add_header Access-Control-Allow-Headers "deviceType,token, authorization, content-type";
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods GET,POST,PUT,DELETE,OPTIONS;
            add_header Access-Control-Allow-Headers "deviceType,token, authorization, content-type";
            return 204;
        }
        proxy_pass         http://127.0.0.1:7780/;
        proxy_redirect     off;
        proxy_set_header   Host              $http_host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Host  $server_name;
        proxy_set_header   X-Forwarded-Proto $scheme;

        proxy_hide_header Access-Control-Allow-Origin;
        proxy_hide_header Access-Control-Allow-Methods;
        proxy_hide_header Access-Control-Allow-Headers;

        access_log      /opt/nginx-logs/api-gateway.access.log seatableformat;
        error_log       /opt/nginx-logs/api-gateway.error.log;
    }
}
"""

    config = {
        'server_name': os.environ['SEATABLE_SERVER_HOSTNAME'],
    }

    if not os.path.exists(path):
        logger.info(f'Generating {os.path.basename(path)} since it does not exist yet')
    else:
        logger.info(f'Updating {os.path.basename(path)}')

    with open(path, 'w') as file:
        # Use lstrip() to remove leading whitespace
        file.write(config_template.lstrip() % config)

if __name__ == '__main__':
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

    # Check that required environment variables are set
    for variable in REQUIRED_VARIABLES:
        if os.environ.get(variable) is None:
            logger.error('Error: Variable "%s" must be provided', variable)
            sys.exit(1)

    # TODO: Goal: Only template configuration files if services are enabled through "ENABLE_" variables
    generate_conf_file(path=SEAFILE_CONF_PATH, prefix='SEAFILE__')
    generate_conf_file(path=CCNET_CONF_PATH, prefix='CCNET__')
    generate_dtable_web_settings_file(path=DTABLE_WEB_CONF_PATH)
    generate_gunicorn_config_file(path=GUNICORN_CONF_PATH)
    generate_dtable_server_config_file(path=DTABLE_SERVER_CONFIG_PATH)
    generate_conf_file(path=DTABLE_DB_CONF_PATH, prefix='DTABLE_DB__')
    generate_conf_file(path=DTABLE_STORAGE_SERVER_CONF_PATH, prefix='DTABLE_STORAGE_SERVER__')
    generate_conf_file(path=DTABLE_EVENTS_CONF_PATH, prefix='DTABLE_EVENTS__')
    generate_conf_file(path=API_GATEWAY_CONF_PATH, prefix='API_GATEWAY__')

    if os.environ.get('ENABLE_NGINX', 'true').lower() == 'true':
        generate_nginx_conf_file(path=NGINX_CONF_PATH)
