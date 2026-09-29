import logging
from pythonjsonlogger import jsonlogger
from pathlib import Path
import sys,os


def setup_logging():

    log_level = "INFO"

    logger = logging.getLogger() # calling root_logger

    logger.setLevel(log_level) # Setting_up_the_level

    logger.handlers.clear() # Clearing the handler

    formatter = jsonlogger.JsonFormatter(fmt = "%(asctime)s %(levelname)s %(name)s %(message)s")


    # Writing logs in file

    path = Path("logs")
    path.mkdir(exist_ok=True)
    log_file = os.path.join(path,"log.txt")



    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)


    # writing logs in console

    #console_log_handler = logging.StreamHandler(sys.stdout)
    #console_log_handler.setFormatter(formatter)

    #logger.addHandler(console_log_handler)

    return logger









