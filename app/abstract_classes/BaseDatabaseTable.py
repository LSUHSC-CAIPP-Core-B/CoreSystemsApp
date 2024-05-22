from abc import abstractmethod
from io import BytesIO
from typing import IO

import pandas as pd
from app.interfaces.ITable import ITable

class BaseDatabaseTable(ITable):
    @abstractmethod
    def display(Uinputs: str, sort: str, sort_orders: dict[str]) -> dict[any]:
        raise NotImplementedError()
    
    @abstractmethod
    def add() -> None:
        raise NotImplementedError()
    
    @abstractmethod    
    def change() -> None:
        raise NotImplementedError()
    
    @abstractmethod
    def delete() -> None:
        raise NotImplementedError()
    
    @abstractmethod
    def download_CSV(saved_data: dict[any]) -> IO[bytes]:
        df = pd.DataFrame.from_dict(saved_data)
        csv = df.to_csv(index=False)
        
        # Convert the CSV string to bytes and use BytesIO
        csv_bytes = csv.encode('utf-8')
        csv_io = BytesIO(csv_bytes) 
        
        return csv_io
