import logging


def set_logging_level(verbosity_level: int):
    logging_mode = {
        3: logging.NOTSET,
        2: logging.INFO,
        1: logging.CRITICAL,
        0: logging.CRITICAL,
        -1: logging.CRITICAL
    }
    logger = logging.getLogger()
    log_formatter = logging.Formatter("%(asctime)s "
                                      "[%(threadName)-12.12s] "
                                      "[%(levelname)-5.5s]  "
                                      "%(message)s",
                                      datefmt='%H:%M:%S',)
    logging_level = logging_mode[verbosity_level]
    console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging_level)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)
    logger.setLevel(logging_level)
