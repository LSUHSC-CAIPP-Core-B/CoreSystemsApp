from abc import ABC, abstractmethod
from typing import IO

class ITable(ABC):
    @abstractmethod
    def display() -> None:
        raise NotImplementedError
    
    @abstractmethod
    def add() -> None:
        raise NotImplementedError
    
    @abstractmethod
    def change() -> None:
        raise NotImplementedError
    
    @abstractmethod
    def delete() -> None:
        raise NotImplementedError

    @abstractmethod
    def download_CSV(saved_data: dict[any]) -> IO[bytes]:
        raise NotImplementedError()