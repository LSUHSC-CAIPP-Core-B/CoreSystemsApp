from abc import ABC, abstractmethod
from typing import IO

class ITable(ABC):
    @abstractmethod
    def display(self) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def add(self) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def change(self) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def delete(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def download_CSV(self, saved_data: dict) -> IO[bytes]:
        raise NotImplementedError()