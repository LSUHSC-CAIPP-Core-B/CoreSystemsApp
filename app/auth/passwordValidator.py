class PasswordValidator:
    """ This class is used to ensure that a password 
    is correct length and contains a certain number 
    of digits and special characters

    Forces keyword arguments for initialization

    :param minChar: minimum characters a password is allowed to have
    :param maxChar: maximum characters a password is allowed to have
    :param specialCharCount: amount of special characters (#,$,!) 
    a password must have
    :param digitCount: amount of digits a password must have
    """    

    minChar = 0; maxChar = 0; specialCharCount = 0; digitCount = 0

    def __init__(self, *, minChar:int, maxChar:int, specialCharCount:int, digitCount:int) -> None:
        self.minChar = minChar
        self.maxChar = maxChar
        self.specialCharCount = specialCharCount
        self.digitCount = digitCount
        pass

    def isValidPassword(self, string:str) -> bool:
        if not string:
            return False
        
        if string.isspace():
            return False
        
        string = string.strip()
        if len(string) < self.minChar and len(string) > self.maxChar:
            return False

        return self.__containsSpecialChar(string) and self.__containsDigit(string)

    def __containsSpecialChar(self, string:str) -> bool:
        count = 0
        for c in string:
            if not c.isalpha() and not c.isdigit():
                count+=1
                if count == self.specialCharCount:
                    return True
        return False

    def __containsDigit(self, string:str) -> bool:
        count = 0
        for c in string:
            if c.isdigit():
                count+=1
                if count == self.digitCount:
                    return True
        return False
