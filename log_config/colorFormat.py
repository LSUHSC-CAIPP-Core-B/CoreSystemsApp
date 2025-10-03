import logging

import colorama
from colorama import Fore, Style

colorama.init()

# Defines colors for different log levels
LOG_COLORS = {
    logging.DEBUG: Fore.BLUE + Style.BRIGHT,
    logging.INFO: Fore.GREEN + Style.BRIGHT,
    logging.WARNING: Fore.YELLOW + Style.BRIGHT,
    logging.ERROR: Fore.RED + Style.BRIGHT,
    logging.CRITICAL: Fore.RED + Style.BRIGHT + Style.BRIGHT,
}

class ColoredFormatter(logging.Formatter):
    """A custom logging formatter that adds color codes to log messages based on their severity level.

    This formatter uses `colorama` to apply colors to log messages. Different colors are used for different log levels.
    """
    
    def format(self, record) -> str:
        """Gets the color for the current log level

        Uses the base class to format the message

        Then adds the color to the formatted message
        :param record: _description_
        :type record: _type_
        :return: returns a single formatted string that includes the color codes and the log message
        :rtype: str
        """        
        log_color = LOG_COLORS.get(record.levelno, Fore.WHITE + Style.BRIGHT)
        message = super().format(record)
        return f"{log_color}{message}{Style.RESET_ALL}"