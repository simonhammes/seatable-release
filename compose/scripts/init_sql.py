import logging
import os
import time
import sys
import pymysql

logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S', stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger()

DB_HOST = os.getenv('DB_HOST', 'db')
DB_USER = os.environ.get('DB_USER', 'root')
DB_ROOT_PASSWD = os.getenv('DB_ROOT_PASSWD', '')

CCNET_DB_NAME = 'ccnet_db'
SEAFILE_DB_NAME = 'seafile_db'
DTABLE_DB_NAME = 'dtable_db'

CCNET_SQL_PATH = '/opt/seatable/seatable-server-latest/sql/mysql/ccnet.sql'
SEAFILE_SQL_PATH = '/opt/seatable/seatable-server-latest/sql/mysql/seafile.sql'
DTABLE_SQL_PATH = '/opt/seatable/seatable-server-latest/sql/mysql/dtable.sql'

def wait_for_mysql():
    while True:
        try:
            connection = pymysql.connect(host=DB_HOST, port=3306, user='root', passwd=DB_ROOT_PASSWD)
        except Exception as e:
            print ('waiting for mysql server to be ready: %s', e)
            time.sleep(2)
            continue
        print('mysql server is ready')
        connection.close()
        return

def create_database(connection: pymysql.Connection, database: str):
    cursor = connection.cursor()
    sql = f'CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET UTF8'

    try:
        affected_rows = cursor.execute(sql)
    except Exception as e:
        logger.error('Failed to create database %s: %s', database, e)
        sys.exit(1)
    finally:
        cursor.close()

    if affected_rows == 0:
        logger.info('Database "%s" already exists', database)
    elif affected_rows == 1:
        logger.info('Successfully created database "%s"', database)

def import_sql_file(connection: pymysql.Connection, file: str):
    cursor = connection.cursor()

    with open(file, 'r') as fp:
        content = fp.read()

    sqls = [line.strip() for line in content.split(';') if line.strip()]
    for sql in sqls:
        try:
            cursor.execute(sql)
        except Exception as e:
            logger.error('Failed to import "%s": %s', os.path.basename(file), e)
            sys.exit(1)

    connection.commit()

    logger.info('Successfully imported "%s"', os.path.basename(file))

if __name__ == '__main__':
    wait_for_mysql()

    try:
        connection = pymysql.connect(host=DB_HOST, port=3306, user=DB_USER, passwd=DB_ROOT_PASSWD)
    except Exception as e:
        logger.error('Failed to connect to mysql server using user "%s" and password "***": %s', DB_USER, e.args[1])
        sys.exit(1)

    databases = [CCNET_DB_NAME, SEAFILE_DB_NAME, DTABLE_DB_NAME]
    for database in databases:
        create_database(connection, database)

    # TODO: Is there a particular reason why the code does not use Django's migration tooling?
    # In my opinion this would make database upgrades (between SeaTable versions) a lot easier.

    connection.select_db(CCNET_DB_NAME)
    import_sql_file(connection, CCNET_SQL_PATH)

    connection.select_db(SEAFILE_DB_NAME)
    import_sql_file(connection, SEAFILE_SQL_PATH)

    connection.select_db(DTABLE_DB_NAME)
    import_sql_file(connection, DTABLE_SQL_PATH)

    # TODO: Create avatars table for dtable-web? Is this even possible in SeaTable?

    connection.close()
