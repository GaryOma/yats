import logging
import logging.handlers
import threading


def listener_configurer():
    root = logging.getLogger()
    file_handler = logging.handlers.RotatingFileHandler('mptest.log', 'a', 300, 10)
    console_handler = logging.StreamHandler()
    log_formatter = logging.Formatter("%(asctime)s "
                                      "[%(threadName)-12.12s] "
                                      "[%(levelname)-5.5s]  "
                                      "%(message)s",
                                      datefmt='%H:%M:%S',)
    file_handler.setFormatter(log_formatter)
    console_handler.setFormatter(log_formatter)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

# This is the listener process top-level loop: wait for logging events
# (LogRecords)on the queue and handle them, quit when you get a None for a
# LogRecord.


def listener_process(queue, configurer):
    listener_configurer()
    while True:
        try:
            record = queue.get()
            if record is None:
                # We send this as a sentinel to tell the listener to quit.
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except Exception:
            import sys
            import traceback
            print('Whoops! Problem:', file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

# The worker configuration is done at the start of the worker process run.
# Note that on Windows you can't rely on fork semantics, so each process
# will run the logging configuration code when it starts.


def logger_configurer(queue):
    root = logging.getLogger()
    if len(root.handlers) > 1:
        return
    h = logging.handlers.QueueHandler(queue)  # Just the one handler needed
    root.addHandler(h)
    # send all messages, for demo; no other level or filter logic applied.
    root.setLevel(logging.DEBUG)

# This is the worker process top-level loop, which just logs ten events with
# random intervening delays before terminating.
# The print messages are just so you know it's doing something!


def worker_process(queue):
    logger_configurer(queue)


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
