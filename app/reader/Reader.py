import pandas as pd

class Reader:
    """
    Class to read/save to/delete from .csv data file

    filename: path to csv to work with
    """
    def __init__(self, filename) -> None:
        self.filename = filename

    def getRawDataCSV(self, headers = True, dict = False):
        """
        Get data from file as it is

        headers (bool): if there are headers to be read into header row
        dict (bool): if convert pandas DF to list of dictionaries

        return: DataFrame or dict of data
        """
        if headers:
            df = pd.read_csv(self.filename)
            if dict:
                df = df.to_dict('records')
        else:
            df = pd.read_csv(self.filename, header=None)
            if dict:
                df = df.to_dict('records')

        return df
    
    def formatRawData(self, df, nRows=1, nCols=1):
        """
        Custom function to format CAIPP_Order.csv file

        df (pandas.DataFrame): data to format
        nRows (int): number of rows to ommit during read
        nCols (int): number of cols to ommit during read

        return: formatted DataFrame data
        """
        # erase first col and row (data not for view)
        df = df.T.iloc[nRows: , nCols:]
        headers = df.iloc[0]
        df = df[1:]
        df.columns = headers

        # erase unnecessary square brackets
        df = df.map(lambda x : str(x)[2:-2] if str(x)[:2] == "['" else x)
        # replace nan to blank space
        df = df.map(lambda x : '-' if str(x) == 'nan' else x)

        return df
    
    def formatRawData2(self, df, nRows=1, nCols=1):
        """
        Custom function to format CAIPP_Order.csv file

        df (pandas.DataFrame): data to format
        nRows (int): number of rows to ommit during read
        nCols (int): number of cols to ommit during read

        return: formatted DataFrame data
        """
        # erase first col and row (data not for view)
        df = df.T.iloc[nRows: , nCols:]
        headers = df.iloc[0]
        df = df[1:]

        df.columns = headers

        # erase unnecessary square brackets and apostrophes but keep the comas where need be
        # transformstring that has an opening square bracket into list of strings separated w ith comas (ex. ["'qw'"," 'we'"," 'rty'"], type: list)
        df = df.map(lambda x : str(x)[1:-1].split(",") if str(x)[:2] == "['" else x)
        # transform every list; clear apostrophes and white spaces; visual transformations (ex. ['qw, ', 'we, ', 'rty, '], type: list)
        df = df.map(lambda x :  [e.strip()[1:-1] + ", " for e in x] if type(x) == list else x)
        # join each list into string (ex. qw, we, rty, type: str)
        df = df.map(lambda x :  "".join(x)[:-2] if type(x) == list else x)
        # replace nan to blank space
        df = df.map(lambda x : '-' if str(x) == 'nan' else x)

        return df

    def getFormattedDataCSV(self, withRaw = False, headers = False):
        """
        Read data and format it 

        withRaw (bool): if to include raw unformatted data
        headers (bool): if there are headers to be read into header row

        return: dict of formatted data is specified with raw DataFrame
        """
        # read csv, headers has to be False to work with CAIPP_Orders.csv data format
        df = self.getRawDataCSV(headers=headers)
        if withRaw:
            df_base = df

        df = self.formatRawData2(df)

        # create list of dicts
        df_dict = df.to_dict('records')
        if withRaw:
            return df_dict, df_base
        else:
            return df_dict
        
    def saveDataCSV(self, updated_dict, unprocessed_df):
        """
        Update data in csv file with new dict, additional formatting steps has to be done to match CAIPP_Order.csv format

        updated_dict (dict): dict with updated data
        unprocessed_df (DataFrame): 
        """
        # save updated data
        output_df = pd.DataFrame.from_dict(updated_dict).T.reset_index()

        # enter QID back to new data
        first_column = []
        for index in unprocessed_df.iloc[1:, 0]:
            first_column.append(str(index))
        output_df = output_df.set_axis(first_column)
        output_df.reset_index(inplace=True)

        # enter Question# back to new data
        first_row = []
        for header in unprocessed_df.iloc[0, :]:
            first_row.append(str(header))
        output_df.columns.values[:] = first_row

        # save to file, header and index configuration ot match CAIPP_Order.csv format
        output_df.to_csv(self.filename, header=True, index=False)
        
    def deleteDataCSV(self, unprocessed_df, id):
        """
        Delete order in database

        unporcessed_df (DataFrame): Frame in which to delete order
        id (int): id at which to erase order
        """
        # get column to delete name rom id
        column_to_delete = unprocessed_df.columns.values[id]
        # delete
        unprocessed_df = unprocessed_df.drop(column_to_delete, axis=1)
        unprocessed_df.to_csv(self.filename, header=True, index=False)
        
    