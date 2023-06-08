import logging
from contextlib import contextmanager
from logging.handlers import QueueListener, QueueHandler, RotatingFileHandler
from queue import Queue


@contextmanager
def prepare_background_logging(log_path):
    logger = logging.getLogger()
    logger.handlers = []
    log_queue = Queue(-1)
    queue_handler = QueueHandler(log_queue)
    logger.addHandler(queue_handler)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S %Z')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    file_handler = RotatingFileHandler(log_path, maxBytes=1024 * 1024 * 1024, backupCount=12)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.ERROR)

    listener = QueueListener(log_queue, console_handler, file_handler)
    listener.start()
    try:
        yield
    except Exception as e:
        logger.error(str(e))
        raise e
    finally:
        listener.stop()
