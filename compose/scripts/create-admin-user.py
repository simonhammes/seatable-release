#!/usr/bin/env python3

import logging
import os
import subprocess
import sys
import pymysql

logger = logging.getLogger('setup-databases')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

DB_HOST = os.getenv('DB_HOST', 'db')
DB_USER = os.environ.get('DB_USER', 'root')
DB_ROOT_PASSWD = os.getenv('DB_ROOT_PASSWD', '')

DTABLE_DB_NAME = 'dtable_db'

if __name__ == '__main__':
    email = os.environ.get('SEATABLE_ADMIN_EMAIL')
    if not email:
        logger.error('$SEATABLE_ADMIN_EMAIL must be provided')
        sys.exit(1)

    password = os.environ.get('SEATABLE_ADMIN_PASSWORD')
    if not password:
        logger.error('$SEATABLE_ADMIN_PASSWORD must be provided')
        sys.exit(1)

    try:
        # Create connection
        connection = pymysql.connect(host=DB_HOST, port=3306, user=DB_USER, passwd=DB_ROOT_PASSWD, database=DTABLE_DB_NAME)
    except Exception as e:
        logger.error('Failed to connect to mysql server using user "%s" and password "***": %s', DB_USER, e.args[1])
        sys.exit(1)

    try:
        # Check if admin user already exists
        cursor = connection.cursor()
        rows = cursor.execute("SELECT * FROM profile_profile WHERE contact_email = %s", email)
    except Exception as e:
        logger.error('Failed to query profile_profile table for existing admin user: %s', e)
        connection.close()
        sys.exit(1)

    connection.close()

    if rows >= 1:
        # TODO: Update password if password has changed?
        logger.info('Admin user %s already exists', email)
        sys.exit(0)

    logger.info('Creating admin user %s...', email)
    process = subprocess.run(['/templates/seatable.sh', 'auto-create-superuser'], capture_output=True)

    if process.returncode != 0:
        logger.error('Could not create admin user, check init.log')
        sys.exit(1)

    logger.info('Successfully created admin user')
