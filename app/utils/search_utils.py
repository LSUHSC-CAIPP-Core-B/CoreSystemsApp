from rapidfuzz import fuzz, utils
import pandas as pd

class search_utils:
    @staticmethod
    def search_data(Uinputs:list, columns_to_check:list, threshold:int, SqlData: pd.DataFrame, columns_rename:dict=None) -> dict:
        '''
        Takes in user inputs, columns to check, threshold,
        Sql dataframe and returns a dictionary of results (list of dictionaries)

        Uinputs(list): Inputs used
        columns_to_checks(list): All possible inputs
        threshold(int): Search Accuracy 0-100 
        SqlData(pd.Dataframe): Data thats being searched
        '''    
        matches_per_input: list = [set() for _ in Uinputs]  # List of sets, one for each input

        for input_index, i in enumerate(Uinputs):
            for index, row in SqlData.iterrows():
                for column in columns_to_check:
                    if fuzz.ratio(i, row[column]) > threshold:
                        matches_per_input[input_index].add(index)  # Adds row index to the set for this input
                        break  # No need to check other columns for this input

        # Finds the intersection of all sets to ensure each input has at least one matching column in the row
        all_matches = set.intersection(*matches_per_input) if matches_per_input else set()
        
        if columns_rename != None:
            SqlData.rename(columns=columns_rename, inplace=True)
        
        filtered_df = SqlData.loc[list(all_matches)]
        return filtered_df.to_dict(orient='records')
    
    @staticmethod
    def sort_searched_data(Uinputs:list, columns_to_check:list, threshold:int, SqlData: pd.DataFrame, sort_by:list, columns_rename:dict=None) -> dict:
        data = SqlData
        data['Target ratio'] = data.apply(lambda x: round(fuzz.ratio(utils.default_process(x.Target_Name), utils.default_process(Uinputs[1])), 2), axis=1).to_list()

        data['Company Ratio'] = data.apply(lambda x: round(fuzz.ratio(utils.default_process(x.Company_name), utils.default_process(Uinputs[0])), 2), axis=1).to_list()

        data['Species Ratio'] = data.apply(lambda x: round(fuzz.ratio(utils.default_process(x.Target_Species), utils.default_process(Uinputs[2])), 2), axis=1).to_list()

        data = data.loc[(data['Target ratio'] > threshold) | (data['Company Ratio'] > threshold) | (data['Species Ratio'] > threshold)]
        df = data.sort_values(by=['Target ratio','Company Ratio', 'Species Ratio', sort_by], ascending=[False, False, True, True])
        df = df.drop(columns=['Target ratio','Company Ratio', 'Species Ratio'])
    
        if columns_rename != None:
            df.rename(columns=columns_rename, inplace=True)

        return df.to_dict(orient='records')