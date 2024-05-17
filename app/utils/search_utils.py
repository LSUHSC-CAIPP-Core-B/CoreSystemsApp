from fuzzywuzzy import fuzz
import pandas as pd

class search_utils:
    @staticmethod
    def search_data(Uinputs:list, columns_to_check:list, threshold:int, SqlData: pd.DataFrame) -> dict:
        '''
        Takes in user inputs, columns to check, threshold,
        Sql dataframe and returns a dictionary of results (list of dictionaries)

        Uinputs(list): Inputs used
        columns_to_checks(list): All possible inputs
        threshold(int): Search Accuracy 0-100 
        SqlData(pd.Dataframe): Data thats being searched
        '''
        matches_per_input = [set() for _ in Uinputs]  # List of sets, one for each input

        for input_index, i in enumerate(Uinputs):
            for index, row in SqlData.iterrows():
                for column in columns_to_check:
                    if fuzz.ratio(i, row[column]) > threshold:
                        matches_per_input[input_index].add(index)  # Adds row index to the set for this input
                        break  # No need to check other columns for this input

        # Finds the intersection of all sets to ensure each input has at least one matching column in the row
        all_matches = set.intersection(*matches_per_input) if matches_per_input else set()
        SqlData.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
        filtered_df = SqlData.loc[list(all_matches)]
        return filtered_df.to_dict(orient='records')