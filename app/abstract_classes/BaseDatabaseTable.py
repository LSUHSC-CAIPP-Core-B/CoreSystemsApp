from abc import abstractmethod
from io import BytesIO
from typing import IO
from typing_extensions import override

import pandas as pd
from app.interfaces.ITable import ITable

class BaseDatabaseTable(ITable):
    """Abstract class

    For tables that display database information

    :param ITable: interface for tables
    :type ITable: type
    """    

    @override
    def display(self, Uinputs: str, sort: str, sort_orders: dict) -> dict[any]:
        raise NotImplementedError()
    
    @abstractmethod
    def add(self, params:dict) -> None:
        raise NotImplementedError()
    
    @abstractmethod    
    def change(self, params:dict) -> None:
        raise NotImplementedError()
    
    @abstractmethod
    def delete(self, primary_key) -> None:
        raise NotImplementedError()
    
    @override
    def download_CSV(self, saved_data: dict) -> IO[bytes]:
        df = pd.DataFrame.from_dict(saved_data)
        csv = df.to_csv(index=False)
        
        # Convert the CSV string to bytes and use BytesIO
        csv_bytes = csv.encode('utf-8')
        csv_io = BytesIO(csv_bytes) 
        
        return csv_io
