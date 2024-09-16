#!/bin/bash

function stop_server() {
    pkill -9 -f seaf-server
    pkill -9 -f gunicorn
    pkill -9 -f main.py
    pkill -9 -f dist/src/index.js
    pkill -9 -f dtable-db
    pkill -9 -f dtable-storage-server
    pkill -9 -f dist-slave/bin/www.js
    pkill -9 -f api-gateway

    pkill -9 -f monitor.sh

    rm -f /opt/seatable/pids/*.pid
}

function set_env() {
    export SRC_DIR=/opt/seatable/seatable-server-latest
    export LD_LIBRARY_PATH=/opt/seatable/seatable-server-latest/seafile/lib/:/usr/lib/x86_64-linux-gnu/nss
    export PYTHONPATH=/opt/seatable/seatable-server-latest/dtable-web/thirdpart:/opt/seatable/seatable-server-latest/seafile/lib/python3/site-packages:/opt/seatable/seatable-server-latest/dtable-events
    export PATH=/opt/seatable/seatable-server-latest/seafile/bin/:/opt/seatable/seatable-server-latest/dtable-web/thirdpart/bin:$PATH

    export CCNET_CONF_DIR=/opt/seatable/ccnet
    export SEAFILE_CONF_DIR=/opt/seatable/seafile-data
    export SEAFILE_CENTRAL_CONF_DIR=/opt/seatable/conf
    export DTABLE_SERVER_CONFIG=/opt/seatable/conf/dtable_server_config.json
    export DTABLE_SERVER_SLAVE_CONFIG=/opt/seatable/conf/dtable_server_slave_config.json
    export DTABLE_SERVER_CLUSTER_LOCAL_INFO=/opt/seatable/conf/dtable_server_cluster_local_info.json
    export SEAHUB_LOG_DIR=/opt/seatable/logs
    export LOG_DIR=/opt/seatable/logs
    export DTABLE_WEB_DIR=/opt/seatable/seatable-server-latest/dtable-web
    export HOME=/root
}

function run_python_wth_env() {
    set_env
    python3 ${*:2}
}

function create_superuser() {
    set_env
    cd /opt/seatable/seatable-server-latest/dtable-web
    python3 manage.py createsuperuser
}

function auto_create_superuser() {
    set_env
    cd /opt/seatable/seatable-server-latest/dtable-web

    if [[ $SEATABLE_ADMIN_EMAIL && $SEATABLE_ADMIN_PASSWORD ]] ;then
        if [[ ${*:2} ]]; then
            while [ 1 ]; do
                name="dtable-web"
                python3 /templates/monitor_ping.py $name
                return_code=$?
                if [ $return_code -ne 0 ]; then
                    echo "Waiting dtable-web" &>> /opt/seatable/logs/init.log
                    sleep 1
                else
                    echo "dtable-web ready" &>> /opt/seatable/logs/init.log
                    break
                fi
            done
        fi
        python3 manage.py createsuperuser --noinput  --username ${SEATABLE_ADMIN_EMAIL} --email ${SEATABLE_ADMIN_EMAIL} --password ${SEATABLE_ADMIN_PASSWORD} &>> /opt/seatable/logs/init.log
    else
        echo "auto create superuser failed, SEATABLE_ADMIN_EMAIL or SEATABLE_ADMIN_PASSWORD is not set" &>> /opt/seatable/logs/init.log
    fi
}

function check_folder() {
    if [[ ! -e /opt/seatable/conf ]]; then
        echo 'do not find /opt/seatable/conf path'
        exit 1
    fi
}

function check_license() {
    if [[ ! -e /opt/seatable/seatable-license.txt ]]; then
        if [[ -f /shared/seatable/seatable-license.txt ]]; then
            ln -s /shared/seatable/seatable-license.txt /opt/seatable/seatable-license.txt
        else
            echo
            echo "Missing SeaTable License!"
            echo
            echo "Please see https://manual.seatable.io/docker/Enterprise-Edition/Deploy%20SeaTable-EE%20with%20Docker/#activating-the-seatable-license"
            echo
            exit 1
        fi
    fi

    wait

    if [[ -e /opt/seatable/seatable-license.txt ]]; then
        mode=$(cat /shared/seatable/seatable-license.txt | grep "Mode" | awk -F '=' '{gsub(/"/, "", $2);print $2}')
        mode_str=`echo $mode`
        expiration=$(cat /shared/seatable/seatable-license.txt | grep "Expiration" | awk -F '=' '{gsub(/"/, "", $2);print $2}')
        expired_time=`date -d "$expiration" +%s`
        now=`date +%s`
        if [[ $mode_str != 'life-time' && $now -gt $expired_time ]]; then
            echo
            echo "SeaTable License Expired!"
            echo
            exit 1
        fi
    fi
}

function init_plugins_repo() {
    if [ $ENABLE_DTABLE_WEB = "true" ]; then
        if [ "${SEATABLE_ENV2CONF:-false}" = "true" ]; then
            # Safety first
            set -euo pipefail

            /templates/create-plugins-repository.py

            set +euo pipefail
        else
            if grep -q -F "PLUGINS_REPO_ID" /opt/seatable/conf/dtable_web_settings.py; then
                return 0
            else
                repo_id=$(python -c "from seaserv import seafile_api; repo_id = seafile_api.create_repo('plugins repo', 'plugins repo', 'dtable@seafile'); print(repo_id)")
                echo -e "\nPLUGINS_REPO_ID='"${repo_id}"'" >>/opt/seatable/conf/dtable_web_settings.py
            fi
        fi
    fi
}

function init_gunicorn() {
    if [ $ENABLE_DTABLE_WEB = "true" ]; then
        if [[ ! -f /opt/seatable/conf/gunicorn.py ]]; then
            init
        fi
    fi
}

function read_seatable_controller_conf() {
    export ENABLE_SEAFILE_SERVER=${ENABLE_SEAFILE_SERVER:-true} 
    export ENABLE_DTABLE_WEB=${ENABLE_DTABLE_WEB:-true}
    export ENABLE_DTABLE_SERVER=${ENABLE_DTABLE_SERVER:-true}
    export ENABLE_DTABLE_DB=${ENABLE_DTABLE_DB:-true}
    export ENABLE_DTABLE_STORAGE_SERVER=${ENABLE_DTABLE_STORAGE_SERVER:-true}
    export ENABLE_DTABLE_EVENTS=${ENABLE_DTABLE_EVENTS:-true}
    export DTABLE_EVENTS_TASK_MODE=${DTABLE_EVENTS_TASK_MODE:-all}
    # all, foreground, background
    export DTABLE_SERVER_MEMORY_SIZE=${DTABLE_SERVER_MEMORY_SIZE:-8192}
    export DTABLE_SERVER_PING_TIMEOUT=${DTABLE_SERVER_PING_TIMEOUT:-20}
    export ENABLE_DTABLE_SERVER_SLAVE=${ENABLE_DTABLE_SERVER_SLAVE:-false}
    export DTABLE_SERVER_SLAVE_MEMORY_SIZE=${DTABLE_SERVER_SLAVE_MEMORY_SIZE:-4096}
    export ENABLE_API_GATEWAY=${ENABLE_API_GATEWAY:-true}

    if [[ -f /opt/seatable/conf/seatable-controller.conf ]]; then
        source /opt/seatable/conf/seatable-controller.conf
    fi
}

function start_server() {

    check_folder
    check_license

    stop_server
    sleep 0.5

    set_env

    read_seatable_controller_conf

    init_gunicorn

    if [ $ENABLE_SEAFILE_SERVER = "true" ]; then
        # TODO: All the changes related to stdout also need to be made inside monitor.sh, in case a service is stopped and restarted through monitor.sh

        LOG_TARGET="/opt/seatable/logs/seafile.log"
        if [ "${SEATABLE_LOG_TO_STDOUT:-false}" = "true" ]; then
            LOG_TARGET="/proc/1/fd/1"
        fi

        seaf-server -F /opt/seatable/conf -c /opt/seatable/ccnet -d /opt/seatable/seafile-data -l "${LOG_TARGET}" -L /opt/seatable -P /opt/seatable/pids/seafile.pid - &
        sleep 1
    else
        echo "Skip seafile-server"
    fi

    init_plugins_repo

    if [ $ENABLE_DTABLE_EVENTS = "true" ]; then
        if [ $DTABLE_EVENTS_TASK_MODE = "background" ]; then
            echo "dtable-events in background mode"
        elif [ $DTABLE_EVENTS_TASK_MODE = "foreground" ]; then
            echo "dtable-events in foreground mode"
        fi
        cd /opt/seatable/seatable-server-latest/dtable-events/dtable_events

        if [ "${SEATABLE_LOG_TO_STDOUT:-false}" = "true" ]; then
            python main.py --config-file /opt/seatable/conf/dtable-events.conf --taskmode $DTABLE_EVENTS_TASK_MODE &>> /proc/1/fd/1 &
        else
            python main.py --config-file /opt/seatable/conf/dtable-events.conf --logfile /opt/seatable/logs/dtable-events.log --taskmode $DTABLE_EVENTS_TASK_MODE &>>/opt/seatable/logs/dtable-events.log &
        fi

        sleep 1
    else
        echo "Skip dtable-events"
    fi

    if [ $ENABLE_DTABLE_WEB = "true" ]; then
        cd /opt/seatable/seatable-server-latest/dtable-web

        if [ "${SEATABLE_LOG_TO_STDOUT:-false}" = "true" ]; then
            gunicorn seahub.wsgi:application -c /opt/seatable/conf/gunicorn.py &>> /proc/1/fd/1 &
        else
            gunicorn seahub.wsgi:application -c /opt/seatable/conf/gunicorn.py &
        fi

        sleep 0.2
    else
        echo "Skip dtable-web"
    fi

    if [ $ENABLE_DTABLE_STORAGE_SERVER = "true" ]; then
        cd /opt/seatable/seatable-server-latest/dtable-storage-server
        ./dtable-storage-server -c /opt/seatable/conf/dtable-storage-server.conf & echo $! > /opt/seatable/pids/dtable-storage-server.pid
        sleep 0.2
    else
        echo "Skip dtable-storage-server"
    fi

    if [ $ENABLE_DTABLE_SERVER = "true" ]; then
        cd /opt/seatable/seatable-server-latest/dtable-server

        LOG_TARGET="/opt/seatable/logs/dtable-server.log"
        if [ "${SEATABLE_LOG_TO_STDOUT:-false}" = "true" ]; then
            LOG_TARGET="/proc/1/fd/1"
        fi

        node --max-old-space-size=$DTABLE_SERVER_MEMORY_SIZE dist/src/index.js &>> "${LOG_TARGET}" &
        sleep 0.2
    else
        echo "Skip dtable-server"
    fi

    if [ $ENABLE_DTABLE_DB = "true" ]; then
        cd /opt/seatable/seatable-server-latest/dtable-db
        ./dtable-db -c /opt/seatable/conf/dtable-db.conf & echo $! > /opt/seatable/pids/dtable-db.pid
        sleep 0.2
    else
        echo "Skip dtable-db"
    fi

    if [ $ENABLE_DTABLE_SERVER_SLAVE = "true" ]; then
        cd /opt/seatable/seatable-server-latest/dtable-server
        node --max-old-space-size=$DTABLE_SERVER_SLAVE_MEMORY_SIZE dist-slave/bin/www.js &>>/opt/seatable/logs/dtable-server-slave.log &
        sleep 0.2
        echo "dtable-server-slave started"
    fi

    if [ $ENABLE_API_GATEWAY = "true" ]; then
        cd /opt/seatable/seatable-server-latest/dtable-db
        if [[ -e /opt/seatable/conf/dtable-api-gateway.conf ]]; then
            ./api-gateway -c /opt/seatable/conf/dtable-api-gateway.conf & echo $! > /opt/seatable/pids/api-gateway.pid
        else
            ./api-gateway & echo $! > /opt/seatable/pids/api-gateway.pid
        fi
        sleep 0.2
    else
        echo "Skip api-gateway"
    fi

    LOG_TARGET="/opt/seatable/logs/monitor.log"
    if [ "${SEATABLE_LOG_TO_STDOUT:-false}" = "true" ]; then
        LOG_TARGET="/proc/1/fd/1"
    fi

    /templates/monitor.sh &>> "${LOG_TARGET}" &

    echo
    echo "SeaTable started"
    echo

}

function upgrade_sql() {
    mysql -h $DB_HOST -p$DB_ROOT_PASSWD dtable_db </opt/seatable/seatable-server-latest/sql/mysql/upgrade/${*:2}/dtable.sql
    if [[ -e /opt/seatable/seatable-server-latest/sql/mysql/upgrade/${*:2}/seafile.sql ]]; then
        mysql -h $DB_HOST -p$DB_ROOT_PASSWD seafile_db </opt/seatable/seatable-server-latest/sql/mysql/upgrade/${*:2}/seafile.sql
    fi
    if [[ -e /opt/seatable/seatable-server-latest/sql/mysql/upgrade/${*:2}/ccnet.sql ]]; then
        mysql -h $DB_HOST -p$DB_ROOT_PASSWD ccnet_db </opt/seatable/seatable-server-latest/sql/mysql/upgrade/${*:2}/ccnet.sql
    fi
}

function init_sql() {
    set_env

    python3 /templates/init_sql.py

}

function init() {
    if [[ ! -e /opt/seatable/conf ]]; then
        mkdir /opt/seatable/conf
    fi

    set_env

    python3 /templates/init_config.py

}

function gc() {
    set_env
    /opt/seatable/seatable-server-latest/seaf-gc.sh ${*:2}
}

function backup_all() {
    set_env
    cd /opt/seatable/seatable-server-latest/dtable-web/
    python3 manage.py backup_all_bases
}

function restore_all() {
    set_env
    cd /opt/seatable/seatable-server-latest/dtable-web/
    python3 manage.py restore_all_bases
}

case $1 in
"start")
    start_server
    ;;
"python-env")
    run_python_wth_env "$@"
    ;;
"stop")
    stop_server
    ;;
"superuser")
    create_superuser
    ;;
"auto-create-superuser")
    auto_create_superuser "$@"
    ;;
"init")
    init
    ;;
"init-sql")
    init_sql
    ;;
"upgrade-sql")
    upgrade_sql "$@"
    ;;
"gc")
    gc "$@"
    ;;
"backup-all")
    backup_all
    ;;
"restore-all")
    restore_all
    ;;
*)
    start_server
    ;;
esac
