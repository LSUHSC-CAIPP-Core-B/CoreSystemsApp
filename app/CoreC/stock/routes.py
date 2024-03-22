from flask import render_template, request, redirect, url_for, flash, make_response, jsonify
from flask_paginate import Pagination, get_page_args
from jinja2 import UndefinedError
from app.CoreC.stock import bp
from app.reader import Reader
from app import login_required
import mysql.connector as connection
import pandas as pd
import json
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import pymysql

import re
from datetime import datetime

# Opens Json file
with open('app/Credentials/CoreC.json', 'r') as file:
            config_data = json.load(file)
db_config = config_data.get('db_config')
db_config
db_config = config_data.get('db_config', {})

def toDataframe(query, database_name, params=None):
    """
    Takes in query, database, and parameter and converts query to a dataframe.
    
    query(str): query to convert to dataframe
    database_name(str): database name for connection
    param(str)or(None): Parameter to put in query

    return: dataframe from the query passed
    """
    # TODO: Make more scalable and flexible
    with open('app/Credentials/CoreC.json', 'r') as file:
        config_data = json.load(file)
    db_config = config_data.get('db_config')
    db_config
    db_config = config_data.get('db_config', {})

    try:
        mydb = pymysql.connect(**db_config)
        # Using bind parameters to prevent SQL injection
        result_dataFrame = pd.read_sql_query(query, mydb, params=params)
        
        mydb.close()  # closes the connection
        return result_dataFrame
    except Exception as e:
        print(str(e))
        mydb.close()

@bp.route('/antibodies', methods=['GET', 'POST'])
@login_required(role=["user", "coreC"])
def antibodies_route():
    if request.method == 'POST':
        Company_name = request.form.get('company_name') or ""
        Target_Name = request.form.get('target_name') or ""
        Target_Species = request.form.get('target_species') or ""
        sort = request.form.get('sort') or 'Original'
        panelSelect =  request.form.get('panelSelect') or 'Original'

        # Stores all possible Inputs
        AllUinputs = [Company_name, Target_Name, Target_Species]
        
        # Creates list to store inputs that are being Used
        Uinputs = []
        # Checks which input fields are being used
        for i in AllUinputs:
            if i:
                Uinputs.append(i)

        # Maps sorting options to their corresponding SQL names
        sort_orders = {
            'Price': 'Cost',
            'Catalog Number': 'Catalog_Num',
            'Expiration Date': 'Expiration_Date',
            'Box Name': 'Box_Name'
        }
        # Check if sort is in the dictionary, if not then uses default value
        order_by = sort_orders.get(sort, 'Target_Name')

        # Validate the order_by to prevent sql injection
        if order_by not in sort_orders.values():
            order_by = 'Target_Name'  

        
        query = f"SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 ORDER BY {order_by};"

        # Creates Dataframe
        df = toDataframe(query, 'CoreC')

        SqlData = df
        
        # * Fuzzy Search *
        # Checks whether filters are being used
        # If filters are used then implements fuzzy matching
        if len(Uinputs) != 0:
            columns_to_check = ["Company_name", "Target_Name", "Target_Species"]

            threshold = 70  # Threshold for a match

            for i in Uinputs:
                matches = []
                for index, row in SqlData.iterrows():
                    for column in columns_to_check:
                        if fuzz.ratio(i, row[column]) > threshold:
                            matches.append(index)
                            break  # Stops checking other columns if a match is found for this row
            
            # renaming columns and setting data variable
            SqlData.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
            # Gets the filtered dataframe
            filtered_df = SqlData.loc[matches]
            # Converts to a list of dictionaries
            data = filtered_df.to_dict(orient='records')
            
            # If no match is found displays empty row
            if not data:
                dataFrame = toDataframe("SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 0 AND Catalog_Num = 'N/A' ORDER BY Target_Name;", 'CoreC')
                dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
                data = dataFrame.to_dict('records')
        else: # If no search filters are used
            # renaming columns and setting data variable
            SqlData.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
            # Converts to a list of dictionaries
            data = SqlData.to_dict(orient='records')

    if request.method == 'GET':
        dataFrame = toDataframe("SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, DATE_FORMAT(Expiration_Date, '%m/%d/%Y') AS Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 ORDER BY Target_Name;", 'CoreC')
        dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
        data = dataFrame.to_dict('records')
    
    #number of rows in table
    num_rows = len(data)

    # use to prevent user from caching pages
    response = make_response(render_template("antibodies_stock.html", data=data, list=list, len=len, str=str, num_rows=num_rows))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

        
@bp.route('/addAntibody', methods=['GET', 'POST'])
@login_required(role=["admin"])
def addAntibody():
    if request.method == 'POST':
        box_name = request.form.get('Box Name')
        company_name = request.form.get('Company')
        catalog_num = request.form.get('Catalog Number')
        target_name = request.form.get('Target')
        target_species = request.form.get('Target Species')
        fluorophore = request.form.get('Fluorophore')
        clone = request.form.get('Clone')
        isotype = request.form.get('Isotype')
        size = request.form.get('Size')
        concentration = request.form.get('Concentration')
        expiration_date = request.form.get('Expiration Date')
        titration = request.form.get('Titration')
        cost = request.form.get('Cost')
        included = request.form.get('Included')

        # Making sure catalog number field isnt empty
        if catalog_num == "" or catalog_num.lower() == "n/a":
            flash('Fields cannot be empty')
            return redirect(url_for('stock.addAntibody'))
        
        # Defines the regex pattern for "YYYY-MM-DD"
        datePattern = r"^\d{4}-\d{2}-\d{2}$"
        
        # Checks if the string matches the pattern
        if re.match(datePattern, expiration_date):
            try:
                # Tries to convert the string to a datetime object
                datetime.strptime(expiration_date, "%Y-%m-%d")
                pass  # It's a valid date in the correct format
            except ValueError:
                # The string is in the correct format but not a valid date
                flash('Not a valid Date')
                return redirect(url_for('stock.addAntibody'))
        else:
            # The string does not match the "YYYY-MM-DD" format
            flash('Date must be in "YYYY-MM-DD" format')
            return redirect(url_for('stock.addAntibody'))

        # * Checking to see if included is Yes or No *
        # Finds match using fuzzywuzzy library
        YesScore = fuzz.ratio("yes", included.lower())
        NoScore = fuzz.ratio("no", included.lower())
        threshold = 80
        
        if YesScore >= threshold:
            included = 1
        elif NoScore >= threshold:
            included = 0
        else:
            flash('Included field must be "Yes" or "No"')
            return redirect(url_for('stock.addAntibody'))

        try:
            mydb = pymysql.connect(**db_config)
            cursor = mydb.cursor()

            params = {'BoxParam': box_name,
                      'CompanyParam': company_name, 
                      'catalogNumParam': catalog_num , 
                      'TargetParam': target_name, 
                      'TargetSpeciesParam': target_species, 
                      'flourParam': fluorophore, 
                      'cloneParam': clone, 
                      'isotypeParam': isotype, 
                      'sizeParam': size, 
                      'concentrationParam': concentration, 
                      'DateParam': expiration_date, 
                      'titrationParam': titration, 
                      'costParam': cost, 
                      'includedParam': included}

            # SQL Add query
            query = "INSERT INTO Antibodies_Stock VALUES (null, %(BoxParam)s, %(CompanyParam)s, %(catalogNumParam)s, %(TargetParam)s, %(TargetSpeciesParam)s, %(flourParam)s, %(cloneParam)s, %(isotypeParam)s, %(sizeParam)s, %(concentrationParam)s, %(DateParam)s, %(titrationParam)s, %(costParam)s, null, %(includedParam)s);"

            #Execute SQL query
            cursor.execute(query, params)

            # Commit the transaction
            mydb.commit()

            # Close the cursor and connection
            cursor.close()
            mydb.close()

            # use to prevent user from caching pages
            response = make_response(redirect(url_for('stock.antibodies_route')))
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
            response.headers["Pragma"] = "no-cache" # HTTP 1.0.
            response.headers["Expires"] = "0" # Proxies.
            return response
        except Exception as e:
            print("Something went wrong: {}".format(e))
            return jsonify({'error': 'Failed to add row.'}), 500

    if request.method == 'GET':
        data = {
            "Box Name": "",
            "Company": "",
            "Catalog Number": "",
            "Target": "",
            "Target Species": "",
            "Fluorophore": "",
            "Clone": "",
            "Isotype": "",
            "Size": "",
            "Concentration": "",
            "Expiration Date": "",
            "Titration": "",
            "Cost": "",
            "Included": ""
        }

        # use to prevent user from caching pages
        response = make_response(render_template('add_antibody.html', fields = data))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

@bp.route('/deleteAntibody', methods=['POST'])
@login_required(role=["admin"])
def deleteAntibody():
    primary_key = request.form['primaryKey']

    try:
        mydb = pymysql.connect(**db_config)
        cursor = mydb.cursor()

        # SQL DELETE query
        query = "DELETE FROM Antibodies_Stock WHERE Stock_ID = %s"

        #Execute SQL query
        cursor.execute(query, (primary_key,))

        # Commit the transaction
        mydb.commit()

        # Close the cursor and connection
        cursor.close()
        mydb.close()

        # use to prevent user from caching pages
        response = make_response(redirect(url_for('stock.antibodies_route')))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    except Exception as e:
        print("Something went wrong: {}".format(e))
        return jsonify({'error': 'Failed to delete row.'}), 500

@bp.route('/changeAntibody', methods=['GET', 'POST'])
@login_required(role=["admin"])
def changeAntibody():
    if request.method == 'POST':
        primary_key = request.form.get('primaryKey')
        box_name = request.form.get('Box Name')
        company_name = request.form.get('Company')
        catalog_num = request.form.get('Catalog Number')
        target_name = request.form.get('Target')
        target_species = request.form.get('Target Species')
        fluorophore = request.form.get('Fluorophore')
        clone = request.form.get('Clone')
        isotype = request.form.get('Isotype')
        size = request.form.get('Size')
        concentration = request.form.get('Concentration')
        expiration_date = request.form.get('Expiration Date')
        titration = request.form.get('Titration')
        cost = request.form.get('Cost ($)')
        included = request.form.get('Included')

        # Making sure catalog number field isnt empty
        if catalog_num == "" or catalog_num == "N/A":
            flash('Fields cannot be empty')
            return redirect(url_for('stock.changeAntibody'))
        
        # TODO make date validation into a function
        # Defines the regex pattern for "YYYY-MM-DD"
        datePattern = r"^\d{4}-\d{2}-\d{2}$"
        
        # Checks if the string matches the pattern
        if re.match(datePattern, expiration_date):
            try:
                # Tries to convert the string to a datetime object
                datetime.strptime(expiration_date, "%Y-%m-%d")
                pass  # It's a valid date in the correct format
            except ValueError:
                # The string is in the correct format but not a valid date
                flash('Not a valid Date')
                return redirect(url_for('stock.changeAntibody'))
        else:
            # The string does not match the "YYYY-MM-DD" format
            flash('Date must be in "YYYY-MM-DD" format')
            return redirect(url_for('stock.changeAntibody'))

        # * Checking to see if included is Yes or No
        # Finds match using fuzzywuzzy library
        YesScore = fuzz.ratio("yes", included.lower())
        NoScore = fuzz.ratio("no", included.lower())
        threshold = 80
        
        if YesScore >= threshold:
            included = 1
        elif NoScore >= threshold:
            included = 0
        elif included == '1' or included == '0':
            pass
        else:
            flash('Included field must be "Yes" or "No"')
            return redirect(url_for('stock.changeAntibody'))

    #try:
        mydb = pymysql.connect(**db_config)
        cursor = mydb.cursor()

        params = {'BoxParam': box_name,
                    'CompanyParam': company_name, 
                    'catalogNumParam': catalog_num , 
                    'TargetParam': target_name, 
                    'TargetSpeciesParam': target_species, 
                    'flourParam': fluorophore, 
                    'cloneParam': clone, 
                    'isotypeParam': isotype, 
                    'sizeParam': size, 
                    'concentrationParam': concentration, 
                    'DateParam': expiration_date, 
                    'titrationParam': titration, 
                    'costParam': cost, 
                    'includedParam': included,
                    'Pkey': primary_key}

        # SQL Change query
        query = "UPDATE Antibodies_Stock SET Box_Name = %(BoxParam)s, Company_name = %(CompanyParam)s, Catalog_Num = %(catalogNumParam)s, Target_Name = %(TargetParam)s, Target_Species = %(TargetSpeciesParam)s, Fluorophore = %(flourParam)s, Clone_Name = %(cloneParam)s, Isotype = %(isotypeParam)s, Size = %(sizeParam)s, Concentration = %(concentrationParam)s, Expiration_Date = %(DateParam)s, Titration = %(titrationParam)s, Cost = %(costParam)s,  Included = %(includedParam)s WHERE Stock_ID = %(Pkey)s;"
        #Execute SQL query
        cursor.execute(query, params)

        # Commit the transaction
        mydb.commit()

        # Close the cursor and connection
        cursor.close()
        mydb.close()

        # use to prevent user from caching pages
        response = make_response(redirect(url_for('stock.antibodies_route')))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

    if request.method == 'GET':
        primary_key = request.args.get('primaryKey')
        query = "SELECT Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost, Included FROM Antibodies_Stock WHERE Stock_ID = %s;"
        df = toDataframe(query, 'CoreC', (primary_key,))
        df.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog Number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
        data = df.to_dict()
        
        # use to prevent user from caching pages
        response = make_response(render_template('change_antibody.html', fields = data, pkey = primary_key))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

@bp.route('/stock', methods=['GET', 'POST'])
@login_required(role=["admin"])
def stock():
    if request.method == 'POST':
        company = request.form.get('Company') or ""
        product = request.form.get('Product') or ""
        sort = request.form.get('sort') or "Original"

        # Stores all possible Inputs
        AllUinputs = [company, product]
        
        # Creates list to store inputs that are being Used
        Uinputs = []
        # Checks which input fields are being used
        for i in AllUinputs:
            if i:
                Uinputs.append(i)

        # Maps sorting options to their corresponding SQL names
        sort_orders = {
            'Product': 'Product_Name',
            'Cost': 'Unit_Price'
        }
        # Check if sort is in the dictionary, if not then uses default value
        order_by = sort_orders.get(sort, 'Quantity')

        # Validate the order_by to prevent sql injection
        if order_by not in sort_orders.values():
            order_by = 'Quantity'  
        
        # Dictionary of Parameters
        params = {'CompanyParam': company, 'ProductParam': product}
        
        # Ascending vs Descending
        if sort == "QuantityAscending":
            query = f"SELECT S.Product_Num, O.Product_Name, O.Catalog_Num , O.Company_Name, O.Unit_Price, S.Quantity FROM  Stock_Info S left join Order_Info O on S.Product_Num = O.Product_Num WHERE O.Company_Name != '0' ORDER BY {order_by};"
        else:
            query = f"SELECT S.Product_Num, O.Product_Name, O.Catalog_Num , O.Company_Name, O.Unit_Price, S.Quantity FROM  Stock_Info S left join Order_Info O on S.Product_Num = O.Product_Num WHERE O.Company_Name != '0' ORDER BY {order_by} DESC;"
        
        df = toDataframe(query, 'CoreC')
        SqlData = df
        
        # * Fuzzy Search *
        # Checks whether filters are being used
        # If filters are used then implements fuzzy matching
        if len(Uinputs) != 0:
            columns_to_check = ["Company_Name", "Product_Name"]

            threshold = 45  # Threshold for a match

            for i in Uinputs:
                matches = []
                for index, row in SqlData.iterrows():
                    for column in columns_to_check:
                        if fuzz.ratio(i, row[column]) > threshold:
                            matches.append(index)
                            break  # Stops checking other columns if a match is found for this row
            
            # renaming columns and setting data variable
            df.rename(columns={'Product_Name': 'Product', 'Catalog_Num': 'Catalog Number','Company_Name': 'Company Name', 'Unit_Price': 'Cost'}, inplace=True)
            # Gets the filtered dataframe
            filtered_df = SqlData.loc[matches]
            # Converts to a list of dictionaries
            data = filtered_df.to_dict(orient='records')
            
            # If no match is found displays empty row
            if not data:
                dataFrame = toDataframe("SELECT S.Product_Num, O.Product_Name, O.Catalog_Num , O.Company_Name, O.Unit_Price, S.Quantity FROM  Stock_Info S left join Order_Info O on S.Product_Num = O.Product_Num WHERE O.Company_Name = '0' ORDER BY Quantity;", 'CoreC')
                dataFrame.rename(columns={'Product_Name': 'Product', 'Catalog_Num': 'Catalog Number','Company_Name': 'Company Name', 'Unit_Price': 'Cost'}, inplace=True)
                data = dataFrame.to_dict('records')
        else: # If no search filters are used
            # renaming columns and setting data variable
            SqlData.rename(columns={'Product_Name': 'Product', 'Catalog_Num': 'Catalog Number','Company_Name': 'Company Name', 'Unit_Price': 'Cost'}, inplace=True)
            # Converts to a list of dictionaries
            data = SqlData.to_dict(orient='records')

    if request.method == 'GET':
        dataFrame = toDataframe("SELECT S.Product_Num, O.Product_Name, O.Catalog_Num , O.Company_Name, O.Unit_Price, S.Quantity FROM  Stock_Info S left join Order_Info O on S.Product_Num = O.Product_Num WHERE O.Company_Name != '0' ORDER BY Quantity;", 'CoreC')
        dataFrame.rename(columns={'Product_Name': 'Product', 'Catalog_Num': 'Catalog Number','Company_Name': 'Company Name', 'Unit_Price': 'Cost'}, inplace=True)
        data = dataFrame.to_dict('records') 
    
    #number of rows in table
    num_rows = len(data)

    # use to prevent user from caching pages
    response = make_response(render_template("stock.html", data=data, list=list, len=len, str=str, num_rows=num_rows))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

@bp.route('/addSupply', methods=['GET', 'POST'])
@login_required(role=["admin"])
def addSupply():
    if request.method == 'POST':
        Company_Name = request.form.get('Company Name')
        catalog_num = request.form.get('Catalog Number')
        cost = request.form.get('Cost')
        Product_Name = request.form.get('Product Name')
        Quantity = request.form.get('Quantity')

        # Making sure catalog number field isnt empty
        if catalog_num == "" or catalog_num.lower() == "n/a":
            flash('Fields cannot be empty')
            return redirect(url_for('stock.addSupply'))

        try:
            mydb = pymysql.connect(**db_config)
            cursor = mydb.cursor()

            params = {'CompanyParam': Company_Name, 
                      'catalogNumParam': catalog_num , 
                      'costParam': cost,
                      'ProductParam': Product_Name
                      }
            
            # SQL Add query
            query = "INSERT INTO Order_Info VALUES (null, %(CompanyParam)s, %(catalogNumParam)s, %(costParam)s, %(ProductParam)s);"
            query2 = "INSERT INTO Stock_Info VALUES (LAST_INSERT_ID(), %s);"

            #Execute SQL query
            cursor.execute(query, params)
            cursor.execute(query2, (Quantity,))

            # Commit the transaction
            mydb.commit()

            # Close the cursor and connection
            cursor.close()
            mydb.close()

            # use to prevent user from caching pages
            response = make_response(redirect(url_for('stock.addSupply')))
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
            response.headers["Pragma"] = "no-cache" # HTTP 1.0.
            response.headers["Expires"] = "0" # Proxies.
            return response
        except Exception as e:
            print("Something went wrong: {}".format(e))
            return jsonify({'error': 'Failed to add row.'}), 500

    if request.method == 'GET':
        data = {
            "Company Name": "",
            "Catalog Number": "",
            "Cost": "",
            "Product Name": "",
            "Quantity": "",
        }

        # use to prevent user from caching pages
        response = make_response(render_template('add_supply.html', fields = data))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    
@bp.route('/changeSupply', methods=['GET', 'POST'])
@login_required(role=["admin"])
def changeSupply():
    if request.method == 'POST':
        primary_key = request.form.get('primaryKey')
        Company_Name = request.form.get('Company Name')
        catalog_num = request.form.get('Catalog Number')
        cost = request.form.get('Cost')
        Product_Name = request.form.get('Product')
        Quantity = request.form.get('Quantity')
        
        mydb = pymysql.connect(**db_config)
        cursor = mydb.cursor()

        params = {'CompanyParam': Company_Name, 
                      'catalogNumParam': catalog_num , 
                      'costParam': cost,
                      'ProductParam': Product_Name,
                      'Pkey': primary_key
                      }

        # SQL Change query
        query = "UPDATE Order_Info SET Company_name = %(CompanyParam)s, Catalog_Num = %(catalogNumParam)s, Unit_Price = %(costParam)s, Product_Name = %(ProductParam)s WHERE Order_Info.Product_Num = %(Pkey)s;"
        query2 = "UPDATE Stock_Info SET Quantity = %s WHERE Product_Num = %s;"
        #Execute SQL query
        cursor.execute(query, params)
        cursor.execute(query2, (Quantity, primary_key))

        # Commit the transaction
        mydb.commit()

        # Close the cursor and connection
        cursor.close()
        mydb.close()

        # use to prevent user from caching pages
        response = make_response(redirect(url_for('stock.stock')))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

    if request.method == 'GET':
        primary_key = int(request.args.get('primaryKey'))
        query = "SELECT O.Product_Name, O.Catalog_Num ,O.Company_Name, O.Unit_Price, S.Quantity FROM  Stock_Info S left join Order_Info O on S.Product_Num = O.Product_Num WHERE O.Product_Num = %s ORDER BY Quantity;"
        df = toDataframe(query, 'CoreC', (primary_key,))
        df.rename(columns={'Product_Name': 'Product', 'Catalog_Num': 'Catalog Number','Company_Name': 'Company Name', 'Unit_Price': 'Cost'}, inplace=True)
        data = df.to_dict()
        
        # use to prevent user from caching pages
        response = make_response(render_template('change_supply.html', fields = data, pkey = primary_key))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    
@bp.route('/deleteSupply', methods=['POST'])
@login_required(role=["admin"])
def deleteSupply():
    primary_key = request.form['primaryKey']

    try:
        mydb = pymysql.connect(**db_config)
        cursor = mydb.cursor()

        # SQL DELETE query
        query = "DELETE FROM Order_Info WHERE Product_Num = %s"
        query2 = "DELETE FROM Stock_Info WHERE Product_Num = %s"

        #Execute SQL query
        #! query2 must be executed first because of foreign key constraints
        cursor.execute(query2, (primary_key,))
        cursor.execute(query, (primary_key,))

        # Commit the transaction
        mydb.commit()

        # Close the cursor and connection
        cursor.close()
        mydb.close()

        # use to prevent user from caching pages
        response = make_response(redirect(url_for('stock.stock')))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    except Exception as e:
        print("Something went wrong: {}".format(e))
        return jsonify({'error': 'Failed to delete row.'}), 500