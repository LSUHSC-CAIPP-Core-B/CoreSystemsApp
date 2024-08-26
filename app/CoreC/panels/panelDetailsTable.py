from app.abstract_classes.BaseDatabaseTable import BaseDatabaseTable


class PanelDetailsTable(BaseDatabaseTable):
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