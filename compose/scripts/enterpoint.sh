#!/bin/bash

# log function
function log() {
    local time=$(date +"%F %T")
    echo "$time $1 "
    echo "[$time] $1 " &>> /opt/seatable/logs/init.log
}

if [ "${SEATABLE_ENV2CONF:-false}" = "true" ]; then
    # Safety first
    set -euo pipefail

    # TODO: Remove this horrendous workaround
    log "Patching dtable.sql..."
    # Negative lookahead (?!) to avoid patching again on the next run (does not work with sed)
    perl -i -pe 's/CREATE TABLE(?! IF)/CREATE TABLE IF NOT EXISTS/g' /opt/seatable/seatable-server-latest/sql/mysql/dtable.sql
    sed -i 's/INSERT INTO/INSERT IGNORE INTO/g' /opt/seatable/seatable-server-latest/sql/mysql/dtable.sql

    /templates/seatable.sh init-sql

    log "Generating configuration files based on environment variables..."
    /templates/generate-config-files.py

    log "Successfully generated configuration files!"

    log "Checking dtable_web_settings.py for syntax errors..."
    python3 -m py_compile /opt/seatable/conf/dtable_web_settings.py

    ln -sf /opt/seatable/conf/nginx.conf /etc/nginx/sites-enabled/default

    log "Reloading NGINX..."
    nginx -s reload

    if [[ -f '/opt/seatable/conf/current_version.txt' ]]; then
        # Only write version to file if it did not exist yet since the version is used to check if updates need to be applied
        echo "${server_version}" > /opt/seatable/conf/current_version.txt
    fi

    # Since the rest of the code would have to be modified...
    set +euo pipefail
else
    is_first_start=0
    # init config
    if [ "`ls -A /opt/seatable/conf`" = "" ]; then
        log "Start init"

        is_first_start=1

        /templates/seatable.sh init-sql &>> /opt/seatable/logs/init.log

        /templates/seatable.sh init &>> /opt/seatable/logs/init.log
    else
        log "Conf exists"
    fi
fi


# avatars
if [[ ! -e /shared/seatable/seahub-data/avatars ]]; then
    mkdir -p /shared/seatable/seahub-data/avatars
    cp /opt/seatable/seatable-server-latest/dtable-web/media/avatars/* /shared/seatable/seahub-data/avatars
else
    if [[ ! -f /shared/seatable/seahub-data/avatars/app.png ]]; then
        cp /opt/seatable/seatable-server-latest/dtable-web/media/avatars/app.png /shared/seatable/seahub-data/avatars/app.png
    fi
fi
rm -rf /opt/seatable/seatable-server-latest/dtable-web/media/avatars
ln -sfn /shared/seatable/seahub-data/avatars /opt/seatable/seatable-server-latest/dtable-web/media


# logo
if [[ -e /shared/seatable/seahub-data/custom ]]; then
    ln -sfn /shared/seatable/seahub-data/custom /opt/seatable/seatable-server-latest/dtable-web/media
fi


# check nginx
while [ 1 ]; do
    process_num=$(ps -ef | grep "/usr/sbin/nginx" | grep -v "grep" | wc -l)
    if [ $process_num -eq 0 ]; then
        log "Waiting Nginx"
        sleep 0.2
    else
        log "Nginx ready"
        break
    fi
done

if [[ ! -L /etc/nginx/sites-enabled/default ]]; then
    ln -s /opt/seatable/conf/nginx.conf /etc/nginx/sites-enabled/default
    nginx -s reload
fi


# letsencrypt renew cert 86400*30
if [[ -f /shared/ssl/renew_cert ]]; then
    env > /opt/dockerenv
    sed -i '1,3d' /opt/dockerenv

    cp /shared/ssl/renew_cert /var/spool/cron/crontabs/root
    chmod 600 /var/spool/cron/crontabs/root

    openssl x509 -checkend 2592000 -noout -in /opt/ssl/$SEATABLE_SERVER_HOSTNAME.crt
    if [[ $? != "0" ]]; then
        log "Renew cert"
        /templates/renew_cert.sh
    fi
fi


# update truststore
log "Updating CA certificates..."
update-ca-certificates --verbose &>> /opt/seatable/logs/init.log


# logrotate
if [[ -f /var/spool/cron/crontabs/root ]]; then
    cat /templates/logrotate-conf/logrotate-cron >> /var/spool/cron/crontabs/root
    /usr/bin/crontab /var/spool/cron/crontabs/root
else
    chmod 0644 /templates/logrotate-conf/logrotate-cron
    /usr/bin/crontab /templates/logrotate-conf/logrotate-cron
fi


# auto start
if [[ $SEATABLE_START_MODE = "cluster" ]] || [[ -f /opt/seatable/conf/seatable-controller.conf ]] ;then
    # cluster mode
    log "Start cluster server"
    /templates/seatable.sh start

else
    # auto upgrade sql
    /templates/seatable.sh python-env /templates/upgrade_sql.py &>> /opt/seatable/logs/init.log
    sleep 5

    # auto start
    log "Start server"
    /templates/seatable.sh start

    # init superuser
    # TODO: Should this run every time?
    # if [[ ${is_first_start} -eq 1 ]]; then
        sleep 5
        log "Auto create superuser"
        /templates/seatable.sh auto-create-superuser ${is_first_start} &>> /opt/seatable/logs/init.log &
    # fi

fi

log "For more startup information, please check the /opt/seatable/logs/init.log"


#
log "This is an idle script (infinite loop) to keep the container running."

function cleanup() {
    kill -s SIGTERM $!
    exit 0
}

trap cleanup SIGINT SIGTERM

while [ 1 ]; do
    sleep 60 &
    wait $!
done
