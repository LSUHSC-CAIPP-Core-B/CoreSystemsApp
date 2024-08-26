from abc import ABC, abstractmethod
from typing import IO


class ITable(ABC):
    """Abstract base class that acts as an interface for table operations.

    This interface defines methods for managing table data, including
    displaying, adding, modifying, deleting entries, and downloading
    data in CSV format. Subclasses must implement these methods to
    provide specific functionality.

    :param ABC: Helper class that provides a standard way 
    to create an ABC (Abstract Class) using inheritance
    :type ABC: type
    """
        
    @abstractmethod
    def display(self) -> None:
        raise NotImplementedError()
    
    @abstractmethod
    def add(self) -> None:
        raise NotImplementedError()
    
    @abstractmethod
    def change(self) -> None:
        raise NotImplementedError()
    
    @abstractmethod
    def delete(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def download_CSV(self, saved_data: dict) -> IO[bytes]:
        raise NotImplementedError()