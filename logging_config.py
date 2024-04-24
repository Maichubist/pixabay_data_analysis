import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "handlers": {
        "file_handler": {
            "class": "logging.FileHandler",
            "filename": "app.log",
            "formatter": "my_formatter",
        },
    },
    "formatters": {
        "my_formatter": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "root": {
        "handlers": ["file_handler"],
        "level": "INFO",
    },
}

logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger()