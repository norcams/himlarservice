
import sys
import logging
import ConfigParser

def get_logger(name, log_file, debug=True, loglevel='INFO'):
    logger = logging.getLogger(name)
    logging.captureWarnings(True)
    logger.setLevel(getattr(logging, loglevel))
    fh = logging.FileHandler(log_file)
    fh.setLevel(getattr(logging, loglevel))
    log_format = '%(asctime)s|%(levelname)s|%(message)s [%(module)s.%(funcName)s():%(lineno)d]'
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

def get_config(config, section, option, default):
    try:
        value = config.get(section, option)
        return value
    except ConfigParser.NoOptionError:
        pass # not found
    except ConfigParser.NoSectionError:
        pass # not found
    return default
