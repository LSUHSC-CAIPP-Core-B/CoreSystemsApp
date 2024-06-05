from typing import IO
from typing_extensions import override

from flask import flash
from fuzzywuzzy import fuzz
from app.abstract_classes.BaseDatabaseTable import BaseDatabaseTable
from app.utils.db_utils import db_utils
from app.utils.search_utils import search_utils
from app.utils.logging_utils.logGenerator import Logger
import pymysql


class antibodiesTable(BaseDatabaseTable):
    """ Concrete class
    
    Inherits from abstract class BaseDatabaseTable

    :param BaseDatabaseTable: Abstract Class BaseDatabaseTable
    :type BaseDatabaseTable: type
    """   
    @override
    def display(self, Uinputs: str, sort: str, sort_orders: dict) -> dict:
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

        # Check if sort is in the dictionary, if not then uses default value
    
        order_by = sort_orders.get(sort, 'Target_Name')

        # Validate the order_by to prevent sql injection
        if order_by not in sort_orders.values():
            order_by = 'Target_Name'  

        query = f"SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 ORDER BY {order_by};"


        # Creates Dataframe
        df = db_utils.toDataframe(query,'app/Credentials/CoreC.json')

        SqlData = df
        
        # * Fuzzy Search *
        # Checks whether filters are being used
        # If filters are used then implements fuzzy matching
        if len(Uinputs) != 0:
            columns_to_check = ["Company_name", "Target_Name", "Target_Species"]
            data = search_utils.search_data(Uinputs, columns_to_check, 70, SqlData)
            
            # If no match is found displays empty row
            if not data:
                dataFrame = db_utils.toDataframe("SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 0 AND Catalog_Num = 'N/A' ORDER BY Target_Name;", 'app/Credentials/CoreC.json')
                dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
                data = dataFrame.to_dict('records')
        else: # If no search filters are used
            # renaming columns and setting data variable
            SqlData.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
            # Converts to a list of dictionaries
            data = SqlData.to_dict(orient='records')
        return data

    def add(self, params:dict) -> None:
        mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreC.json'))
        cursor = mydb.cursor()

        # SQL Add query
        query = "INSERT INTO Antibodies_Stock VALUES (null, %(BoxParam)s, %(CompanyParam)s, %(catalogNumParam)s, %(TargetParam)s, %(TargetSpeciesParam)s, %(flourParam)s, %(cloneParam)s, %(isotypeParam)s, %(sizeParam)s, %(concentrationParam)s, %(DateParam)s, %(titrationParam)s, %(costParam)s, null, %(includedParam)s);"

        #Execute SQL query
        cursor.execute(query, params)

        # Commit the transaction
        mydb.commit()

        # Close the cursor and connection
        cursor.close()
        mydb.close()                    

    def change(self, params:dict) -> None:
        mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreC.json'))
        cursor = mydb.cursor()

        # SQL Change query
        query = "UPDATE Antibodies_Stock SET Box_Name = %(BoxParam)s, Company_name = %(CompanyParam)s, Catalog_Num = %(catalogNumParam)s, Target_Name = %(TargetParam)s, Target_Species = %(TargetSpeciesParam)s, Fluorophore = %(flourParam)s, Clone_Name = %(cloneParam)s, Isotype = %(isotypeParam)s, Size = %(sizeParam)s, Concentration = %(concentrationParam)s, Expiration_Date = %(DateParam)s, Titration = %(titrationParam)s, Cost = %(costParam)s,  Included = %(includedParam)s WHERE Stock_ID = %(Pkey)s;"
        #Execute SQL query
        cursor.execute(query, params)

        # Commit the transaction
        mydb.commit()

        # Close the cursor and connection
        cursor.close()
        mydb.close()
    
    def delete(self, primary_key) -> None:
        logFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s - (Line: %(lineno)s [%(filename)s])'
        LogGenerator = Logger(logFormat=logFormat, logFile='application.log')
        logger = LogGenerator.generateLogger()

        mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreC.json'))
        cursor = mydb.cursor()

        # SQL DELETE query
        query = "DELETE FROM Antibodies_Stock WHERE Stock_ID = %s"
        logger.info(f"Executing query: {query} with params: {primary_key}")
        #Execute SQL query
        cursor.execute(query, (primary_key,))

        # Commit the transaction
        mydb.commit()

        # Close the cursor and connection
        cursor.close()
        mydb.close()

        logger.info("Deletion Complete!")

    def isIncludedValidInput(self, included: str) -> str | bool:
        """# * Checking to see if included is Yes or No *
        Finds match using fuzzywuzzy library

        :param included: Included Variable
        :type included: str
        :return: returns string included or boolean false
        :rtype: str | bool
        """        

        YesScore = fuzz.ratio("yes", included.lower())
        NoScore = fuzz.ratio("no", included.lower())
        threshold = 80
        
        if YesScore >= threshold:
            return (included := 1)
        elif NoScore >= threshold:
            return (included := 0)
        else:
            flash('Included field must be "Yes" or "No"')
            return False