from abc import abstractmethod
from io import BytesIO
from typing import IO

import pandas as pd
from typing_extensions import override

from app.interfaces.ITable import ITable

class BaseDatabaseTable(ITable):
    """Abstract class for database tables that display and manage
    database information.

    Inherits from `ITable` and provides a framework for implementing
    database table operations, including adding, changing, deleting
    entries, and downloading data as CSV.
    """    

    @override
    def display(self, Uinputs: str, sort: str) -> dict[any]:
        """Filter and display the table based on user inputs and sorting criteria.

        :param Uinputs: User inputs for filtering the table.
        :type Uinputs: str
        :param sort: Criteria for sorting the table.
        :type sort: str
        :return: Filtered and sorted table data.
        :rtype: dict
        """
        raise NotImplementedError()
    
    @abstractmethod
    def add(self, params:dict) -> None:
        """Execute a query to add an entry to the database.

        :param params: Maps parameter names to corresponding input variable names.
        :type params: dict
        """
        raise NotImplementedError()
    
    @abstractmethod    
    def change(self, params:dict) -> None:
        """Execute a query to modify an existing entry in the database.

        :param params: Maps parameter names to corresponding input variable names.
        :type params: dict
        """
        raise NotImplementedError()
    
    @abstractmethod
    def delete(self, primary_key) -> None:
        """Execute a query to delete an entry from the database based on the primary key.

        :param primary_key: The primary key of the entry to be deleted.
        :type primary_key: _type_
        """
        raise NotImplementedError()
    
    @override
    def download_CSV(self, saved_data: dict, *, dropCol: list[str] = None) -> IO[bytes]:
        """Convert saved data to a CSV file and return it as a byte stream.

        :param saved_data: Dictionary containing the table data to be saved in the CSV file.
        :type saved_data: dict
        :param dropCol: Optional list of columns to remove from the CSV file.
        :type dropCol: List[str], optional
        :return: Byte stream of the CSV file.
        :rtype: IO[bytes]
        """        
        df = pd.DataFrame.from_dict(saved_data)

        if dropCol is not None:
            df.drop(columns=dropCol, inplace=True)

        csv = df.to_csv(index=False)
        
        # Convert the CSV string to bytes and use BytesIO
        csv_bytes = csv.encode('utf-8')
        csv_io = BytesIO(csv_bytes) 
        
        return csv_io

