from app.abstract_classes.BaseDatabaseTable import BaseDatabaseTable
import re


class PanelsTable(BaseDatabaseTable):
    """Concrete class
    
    Inherits from abstract class BaseDatabaseTable

    :param BaseDatabaseTable: _description_
    :type BaseDatabaseTable: _type_
    """

    def display(self, Uinputs: str, sort: str) -> dict:
        return super().display(Uinputs, sort)
    
    def add(self, params: dict) -> None:
        return super().add(params)
    
    def change(self, params: dict) -> None:
        return super().change(params)
    
    def delete(self, primary_key) -> None:
        return super().delete(primary_key)
    
    def get_Valid_db_Name(self, Uinput: str) -> str:
        """Replaces spaces with underscores

        Args:
            Uinput (str): User Input

        Returns:
            str: Valid SQL Name
        """
        if "panel" not in Uinput or "Panel" not in Uinput:
            Uinput = f"{Uinput}_panel"

        Uinput = Uinput.strip()

        if " " in Uinput:
            Uinput = Uinput.replace(' ', '_')
        
        return Uinput
    
    def get_Valid_Panel_Name(self, Uinput: str) -> str:
        """Removes the word panel from the User Input

        Args:
            Uinput (str): User Input

        Returns:
            str: String without the word panel
        """
        insensitiveUinput = Uinput.casefold()

        #patterns to be replaced with a space
        patterns = [' panel ', ' panel', 'panel ', 'panel']
        
        # Combines patterns into a single regex
        regex = '|'.join(re.escape(pattern) for pattern in patterns)
        
        #Perform case-insensitive replacement while preserving original case
        Uinput = re.sub(regex, ' ', Uinput, flags=re.IGNORECASE).strip()

        return Uinput