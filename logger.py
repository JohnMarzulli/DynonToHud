import logging
import threading

logging.basicConfig(
    filename='dynon.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

__logging_lock__ = threading.Lock()


def log(
    text_to_log: str
):
    if text_to_log is None:
        return

    __logging_lock__.acquire()
    try:
        logging.info(text_to_log)
    finally:
        __logging_lock__.release()
