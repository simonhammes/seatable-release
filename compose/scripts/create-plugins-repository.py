#!/usr/bin/env python3

import logging
import os
import pickle
import pymysql
import sys

from base64 import b64encode
from seaserv import seafile_api

logger = logging.getLogger('create-plugins-repository')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

DB_HOST = os.getenv('DB_HOST', 'db')
DB_USER = os.environ.get('DB_USER', 'root')
DB_ROOT_PASSWD = os.getenv('DB_ROOT_PASSWD', '')
DTABLE_DB_NAME = 'dtable_db'

if __name__ == '__main__':
    try:
        connection = pymysql.connect(host=DB_HOST, port=3306, user=DB_USER, passwd=DB_ROOT_PASSWD, database=DTABLE_DB_NAME)
    except Exception as e:
        logger.error('Failed to connect to mysql server using user "%s" and password "***": %s', DB_USER, e.args[1])
        sys.exit(1)

    try:
        # Check if database entry already exists
        # TODO: Race condition if using cluster setup?
        cursor = connection.cursor()
        rows = cursor.execute("SELECT * FROM constance_config WHERE constance_key = 'PLUGINS_REPO_ID'")
    except Exception as e:
        logger.error('Failed to query constance_config table for existing repository ID: %s', e)
        connection.close()
        sys.exit(1)

    if rows >= 1:
        logger.info('constance_config already contains PLUGINS_REPO_ID')
        connection.close()
        sys.exit(0)

    logger.info('Creating plugins repository...')
    repo_id = seafile_api.create_repo('plugins repo', 'plugins repo', 'dtable@seafile')
    logger.info('Successfully created plugins repository "%s"', repo_id)

    # constance values are stored in a serialized manner
    repo_id = b64encode(pickle.dumps(repo_id, protocol=2)).decode()

    logger.info('Storing repository ID in dtable_db.constance_config table...')

    try:
        connection = pymysql.connect(host=DB_HOST, port=3306, user=DB_USER, passwd=DB_ROOT_PASSWD, database=DTABLE_DB_NAME)
    except Exception as e:
        logger.error('Failed to connect to mysql server using user "%s" and password "***": %s', DB_USER, e.args[1])
        sys.exit(1)

    try:
        cursor = connection.cursor()
        sql = "INSERT INTO constance_config(constance_key, value) VALUES ('PLUGINS_REPO_ID', %s)"
        cursor.execute(sql, (repo_id,))
        connection.commit()
    except Exception as e:
        logger.error('Failed to insert repository ID: %s', e)
        sys.exit(1)
    finally:
        connection.close()

    logger.info('Successfully inserted plugins repository ID')
