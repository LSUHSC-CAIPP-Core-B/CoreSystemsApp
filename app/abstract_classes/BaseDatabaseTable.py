from abc import abstractmethod
from io import BytesIO
from typing import IO

import pandas as pd
from typing_extensions import override

from app.interfaces.ITable import ITable


class BaseDatabaseTable(ITable):
    """Abstract class

    For tables that display database information

    :param ITable: interface for tables
    :type ITable: type
    """    

    @override
    def display(self, Uinputs: str, sort: str) -> dict[any]:
        """Filters table then displays it 

        :param Uinputs: User Inputs
        :type Uinputs: str
        :param sort: what to sort by
        :type sort: str
        :param sort_orders: Maps sorting options to their corresponding SQL names
        :type sort_orders: dict
        :return: data
        :rtype: dict
        """
        raise NotImplementedError()
    
    @abstractmethod
    def add(self, params:dict) -> None:
        """Executes query to add an antibody to the database

        :param params: Maps parameter names to corresponding input variable names
        :type params: dict
        """
        raise NotImplementedError()
    
    @abstractmethod    
    def change(self, params:dict) -> None:
        """Executes query to change an antibody in the database

        :param params: Maps parameter names to corresponding input variable names
        :type params: dict
        """
        raise NotImplementedError()
    
    @abstractmethod
    def delete(self, primary_key) -> None:
        """Executes query to delete an antibody from the database

        :param primary_key: primary key
        :type primary_key: _type_
        """
        raise NotImplementedError()
    
    @override
    def download_CSV(self, saved_data: dict) -> IO[bytes]:
        """Takes the saved data and converts it to a 
        dataframe then converts the dataframe to a CSV and
        downloads the CSV file locally on the users computer

        :param saved_data: Data from a table
        :type saved_data: dict
        :return: CSV string in bytes
        :rtype: IO[bytes]
        """        
        df = pd.DataFrame.from_dict(saved_data)
        csv = df.to_csv(index=False)
        
        # Convert the CSV string to bytes and use BytesIO
        csv_bytes = csv.encode('utf-8')
        csv_io = BytesIO(csv_bytes) 
        
        return csv_io