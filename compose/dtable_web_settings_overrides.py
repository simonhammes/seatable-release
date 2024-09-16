SITE_TITLE = '123'

# Logs should go to stdout
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s[%(lineno)s] - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        '': {
            'level': "INFO",
            'handlers': ['console'],
            'propagate': False
        },
        'django.request': {
            'level': "INFO",
            'handlers': ['console'],
            'propagate': False
        },
        'py.warnings': {
            'level': "INFO",
            'handlers': ['console'],
            'propagate': False
        }
    }
}
