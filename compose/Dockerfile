FROM seatable/seatable-enterprise-testing:5.1.4

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
