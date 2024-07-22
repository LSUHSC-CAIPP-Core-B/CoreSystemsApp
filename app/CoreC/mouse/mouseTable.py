from app.abstract_classes.BaseDatabaseTable import BaseDatabaseTable

class mouseTable(BaseDatabaseTable):
    """Concrete class
    
    Inherits from abstract class BaseDatabaseTable

    :param BaseDatabaseTable: Abstract Class BaseDatabaseTable
    :type BaseDatabaseTable: type
    """
    
    def display(self, Uinputs: str, sort: str) -> dict:
        return super().display(Uinputs, sort)
    
    def add(self, params: dict) -> None:
        return super().add(params)
    
    def change(self, params: dict) -> None:
        return super().change(params)
    
    def delete(self, primary_key) -> None:
        return super().delete(primary_key)