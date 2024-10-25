FROM seatable/seatable-enterprise-testing:5.1.9

COPY scripts/* /templates

ARG SETTINGS_FILE=/opt/seatable/seatable-server-latest/dtable-web/seahub/settings.py

# Patch settings.py to add "PLUGINS_REPO_ID" to CONSTANCE_CONFIG (after DTABLE_EXPORT_MAX_SIZE)
RUN sed -i "/\x27DTABLE_EXPORT_MAX_SIZE\x27: (DTABLE_EXPORT_MAX_SIZE, \x27\x27),/a \'PLUGINS_REPO_ID\x27: (None, \x27Help Text\x27)," ${SETTINGS_FILE} && \
    python -m py_compile ${SETTINGS_FILE}

# Patch PLUGINS_REPO_ID import
# TODO: Add error handling if config does not contain PLUGINS_REPO_ID field (would currently throw AttributeError)
RUN sed -i 's/PLUGINS_REPO_ID = settings\.PLUGINS_REPO_ID/from constance import config\nPLUGINS_REPO_ID = getattr(config, \x27PLUGINS_REPO_ID\x27)/g' /opt/seatable/seatable-server-latest/dtable-web/seahub/api2/endpoints/admin/sys_plugins.py && \
    python -m py_compile /opt/seatable/seatable-server-latest/dtable-web/seahub/api2/endpoints/admin/sys_plugins.py && \
    sed -i 's/settings\.PLUGINS_REPO_ID/getattr(config, \x27PLUGINS_REPO_ID\x27)/g' /opt/seatable/seatable-server-latest/dtable-web/seahub/dtable/views.py && \
    python -m py_compile /opt/seatable/seatable-server-latest/dtable-web/seahub/dtable/views.py

###########
# LOGGING #
###########

# Patch dtable-server
RUN sed -i 's/dateFile/stdout/g' /opt/seatable/seatable-server-latest/dtable-server/dist/src/logger.js

# Patch dtable-events (handler, date format, log format)
RUN sed -i 's/handlers\.TimedRotatingFileHandler(log_file, when=\x27MIDNIGHT\x27, interval=1, backupCount=7)/logging\.StreamHandler(sys\.stdout)/g' /opt/seatable/seatable-server-latest/dtable-events/dtable_events/dtable_io/utils.py && \
    sed -i 's/logging\.Formatter(\x27%(asctime)s \[%(levelname)s\] %(message)s\x27)/logging\.Formatter(\x27\[%(asctime)s\] \[%(levelname)s\] %(message)s\x27, datefmt=\x27%Y-%m-%d %H:%M:%S\x27)/g' /opt/seatable/seatable-server-latest/dtable-events/dtable_events/dtable_io/utils.py && \
    sed -i 's/%m\/%d\/%Y/%Y-%m-%d/g' /opt/seatable/seatable-server-latest/dtable-events/dtable_events/app/log.py && \
    sed -i 's/\[%(asctime)s\] %(filename)s\[line:%(lineno)d\] \[%(levelname)s\] %(message)s/[%(asctime)s] [%(levelname)s] %(filename)s[line:%(lineno)d] %(message)s/g' /opt/seatable/seatable-server-latest/dtable-events/dtable_events/app/log.py

# TODO: Check all the '*Timer' classes in dtable-events which start new processes; their stdout/stderr needs to be forwarded to stdout//proc/1/fd/1
# TODO: Test this
RUN find /opt/seatable/seatable-server-latest/dtable-events -type f -exec sed -i 's/output=fp//g' {} \;

# TODO: dtable-db, dtable-storage-server, api-gateway
