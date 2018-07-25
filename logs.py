
import sys
import logging

def get_logger(name, log_file, debug=True, loglevel='INFO'):
    logger = logging.getLogger(name)
    logging.captureWarnings(True)
    logger.setLevel(getattr(logging, loglevel))
    fh = logging.FileHandler(log_file)
    fh.setLevel(getattr(logging, loglevel))
    log_format = '%(asctime)s|%(levelname)s|%(message)s'
    fh.setFormatter(logging.Formatter(log_format))
    logger.addHandler(fh)

    # if debug:
    #     ch = logging.StreamHandler(sys.stdout)
    #     format = '%(message)s [%(module)s.%(funcName)s():%(lineno)d]'
    #     formatter = logging.Formatter(format)
    #     ch.setFormatter(formatter)
    #     ch.setLevel(logging.DEBUG)
    #     logger.addHandler(ch)


    return logger
