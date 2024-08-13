from rapidfuzz import fuzz, utils

class string_utils:
    """Useful string utilities

    :return: 
    :rtype: None
    """
    @staticmethod
    def isValidInput(string:str, expected:str, *, threshold:int=70) -> bool:
        """Checks if the input string matches the expected input

        :param string: Input string to be compared
        :type string: str
        :param expected: expected input string
        :type expected: str
        :param threshold: what the fuzz.ratio should atleast be, defaults to 70
        :type threshold: int, optional
        :return: returns True if the input string matches the expected string
        :rtype: bool
        """
        ProcessedInput = utils.default_process(string)
        ProcessedExpected = utils.default_process(expected)

        if fuzz.ratio(ProcessedInput, ProcessedExpected) >= threshold:
            return True
        return False