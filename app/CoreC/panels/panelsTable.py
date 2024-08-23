from app.abstract_classes.BaseDatabaseTable import BaseDatabaseTable


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
        Uinput = Uinput.lower()

        if "panel" not in Uinput or "Panel" not in Uinput:
            Uinput = f"{Uinput}_panel"

        Uinput = Uinput.strip()

        if " " in Uinput:
            Uinput = Uinput.replace(' ', '_')
        
        return Uinput

    def get_Valid_Panel_Name(self, Uinput: str) -> str:
        if "panel" in Uinput or "Panel" in Uinput:
            Uinput = Uinput.replace('panel', '')
            Uinput = Uinput.replace('Panel', '')

        Uinput = Uinput.strip()
        
        return Uinput