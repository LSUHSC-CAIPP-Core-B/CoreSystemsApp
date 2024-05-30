import logging
from app.utils.logging_utils.colorFormat import ColoredFormatter

class Logger():
    logFormat: str

    def __init__(self, logFormat) -> None:
        self.logFormat = logFormat

    def generateLogger(self) -> type:
        # Creates logger
        logger = logging.getLogger("logger")
        logLevel = logging.DEBUG
        logger.setLevel(logging.DEBUG)

        # Creates console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # Creates formatter
        formatter = ColoredFormatter(self.logFormat,
                                    datefmt='%m/%d/%Y, %I:%M:%S %p')

        # Add formatter to console handler
        ch.setFormatter(formatter)

        # Add console handler to logger
        logger.addHandler(ch)
        return logger