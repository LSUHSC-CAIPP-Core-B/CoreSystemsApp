from flask import render_template, request, redirect, url_for, flash, make_response, jsonify
from flask_paginate import Pagination, get_page_args
from jinja2 import UndefinedError
from app.CoreC.stock import bp
from app.reader import Reader
from app import login_required
import mysql.connector as connection
import pandas as pd

def toDataframe(query, database_name, params=None):
    """
    Takes in query, database, and parameter and converts query to a dataframe.
    
    query(str): query to convert to dataframe
    database_name(str): database name for connection
    param(str)or(None): Parameter to put in query

    return: dataframe from the query passed
    """
    try:
        mydb = connection.connect(host="127.0.0.1", database=database_name, user="root", passwd="FrdL#7329", use_pure=True, auth_plugin='mysql_native_password')
        
        # Using bind parameters to prevent SQL injection
        result_dataFrame = pd.read_sql(query, mydb, params=params)
        
        mydb.close()  # close the connection
        return result_dataFrame
    except Exception as e:
        print(str(e))
        mydb.close()

#information_reader = Reader("PI_ID - PI_ID.csv")
    
@bp.route('/antibodies', methods=['GET', 'POST'])
@login_required(role=["user", "coreC"])
def antibodies_route():
    if request.method == 'POST':
        company_name = request.form.get('company_name') or ""
        target_name = request.form.get('target_name') or ""
        target_species = request.form.get('target_species') or ""
        sort = request.form.get('sort') or 'Original'

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

        # Dictionary of Parameters
        params = {'CompanyParam': company_name, 'TargetParam': target_name, 'TargetSpeciesParam': target_species}
        
        # Checks if value is given
        if company_name and target_name and target_species:
            dataFrame = toDataframe(f"SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, DATE_FORMAT(Expiration_Date, '%m/%d/%Y') AS Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 AND Company_name = %(CompanyParam)s AND (Target_Name = %(TargetParam)s OR Target_Name REGEXP CONCAT('^', %(TargetParam)s, '[a-f]')) AND Target_Species = %(TargerSpeciesParam)s ORDER BY {order_by};", 'antibodies', params)
        elif company_name and target_name:
            dataFrame = toDataframe(f"SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, DATE_FORMAT(Expiration_Date, '%m/%d/%Y') AS Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 AND Company_name = %(CompanyParam)s AND (Target_Name = %(TargetParam)s OR Target_Name REGEXP CONCAT('^', %(TargetParam)s, '[a-f]')) ORDER BY {order_by};", 'antibodies', params)
        elif company_name and target_species:
            dataFrame = toDataframe(f"SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, DATE_FORMAT(Expiration_Date, '%m/%d/%Y') AS Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 AND Company_name = %(CompanyParam)s AND Target_Species = %(TargetSpeciesParam)s ORDER BY {order_by};", 'antibodies', params)
        elif target_name and target_species:
            dataFrame = toDataframe(f"SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, DATE_FORMAT(Expiration_Date, '%m/%d/%Y') AS Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 AND (Target_Name = %(TargetParam)s OR Target_Name REGEXP CONCAT('^', %(TargetParam)s, '[a-f]')) AND Target_Species = %(TargetSpeciesParam)s ORDER BY {order_by};", 'antibodies', params)
        elif company_name:
            param = (company_name,)
            dataFrame = toDataframe(f"SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, DATE_FORMAT(Expiration_Date, '%m/%d/%Y') AS Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 AND Company_name = %s ORDER BY {order_by};", 'antibodies', param)
        elif target_name:
            param = (target_name,)
            dataFrame = toDataframe(f"SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, DATE_FORMAT(Expiration_Date, '%m/%d/%Y') AS Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 AND (Target_Name = %(TargetParam)s OR Target_Name REGEXP CONCAT('^', %(TargetParam)s, '[a-f]')) ORDER BY {order_by};", 'antibodies', params)
        elif target_species:
            param = (target_species,)
            dataFrame = toDataframe(f"SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, DATE_FORMAT(Expiration_Date, '%m/%d/%Y') AS Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 AND Target_Species = %s ORDER BY {order_by};", 'antibodies', param)
        else:# When fields are empty or only sorting
            dataFrame = toDataframe(f"SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, DATE_FORMAT(Expiration_Date, '%m/%d/%Y') AS Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 ORDER BY {order_by};", 'antibodies')

        # renaming columns and setting data variable
        dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
        data = dataFrame.to_dict('records')

    if request.method == 'GET':
        dataFrame = toDataframe("SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, DATE_FORMAT(Expiration_Date, '%m/%d/%Y') AS Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 ORDER BY Target_Name;", 'antibodies')
        dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
        data = dataFrame.to_dict('records')
    
    #number of rows in table
    num_rows = len(data)

    try:
        # use to prevent user from caching pages
        response = make_response(render_template("antibodies_stock.html", data=data, list=list, len=len, str=str, num_rows=num_rows))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    except UndefinedError:
        print("jinja2.exceptions.UndefinedError: list object has no element 0")
        
        dataFrame = toDataframe("SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, DATE_FORMAT(Expiration_Date, '%m/%d/%Y') AS Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 0 AND Catalog_Num = 0;", 'antibodies')
        dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
        data = dataFrame.to_dict('records')
        # use to prevent user from caching pages
        response = make_response(render_template("antibodies_stock.html", data=data, list=list, len=len, str=str))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    
@bp.route('/addAntibody', methods=['GET', 'POST'])
@login_required(role=["admin"])
def addAntibody():
    if request.method == 'POST':
        box_name = request.form.get('Box')
        company_name = request.form.get('Company')
        catalog_num = request.form.get('Catalog Number')
        target_name = request.form.get('Target')
        target_species = request.form.get('Target Species')
        fluorophore = request.form.get('Fluorophore')
        clone = request.form.get('Clone')
        isotype = request.form.get('Isotype')
        size = request.form.get('Clone')
        concentration = request.form.get('Concentration')
        expiration_date = request.form.get('Expiration Date')
        titration = request.form.get('Titration')
        included = request.form.get('Included')
        print(catalog_num)

        if catalog_num == "":
            flash('Fields cannot be empty')
            return redirect(url_for('stock.antibodies_route'))

        # use to prevent user from caching pages
        response = make_response(redirect(url_for('stock.antibodies_route')))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

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
    print(primary_key)

    try:
        mydb = connection.connect(host="127.0.0.1", database="antibodies", user="root", passwd="FrdL#7329", use_pure=True, auth_plugin='mysql_native_password')
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
        box_name = request.form.get('Box')
        company_name = request.form.get('Company')
        catalog_num = request.form.get('Catalog Number')
        target_name = request.form.get('Target')
        target_species = request.form.get('Target Species')
        fluorophore = request.form.get('Fluorophore')
        clone = request.form.get('Clone')
        isotype = request.form.get('Isotype')
        size = request.form.get('Clone')
        concentration = request.form.get('Concentration')
        expiration_date = request.form.get('Expiration Date')
        titration = request.form.get('Titration')
        included = request.form.get('Included')

        # use to prevent user from caching pages
        response = make_response(redirect(url_for('stock.antibodies_route')))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    
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
            "Included": ""
        }

        # use to prevent user from caching pages
        response = make_response(render_template('change_antibody.html', fields = data))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

@bp.route('/panels', methods=['GET', 'POST'])
@login_required(role=["user", "coreC"])
def panels():
    if request.method == 'GET':
        dataFrame = toDataframe("SELECT * FROM panels", 'antibodies')
        data = dataFrame.to_dict('records')
        # use to prevent user from caching pages
        response = make_response(render_template("panels.html", data=data, list=list, len=len, str=str))
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

        if company and product:
            dataFrame = toDataframe(f"SELECT o.Product_Name, o.catalog_num ,o.Company_Name, o.Unit_Price, s.Quantity FROM  stock_info S left join Order_Info O on S.Product_Num = O.Product_Num WHERE Company_Name COLLATE utf8mb4_general_ci LIKE %(CompanyParam)s AND Product_Name COLLATE utf8mb4_general_ci LIKE %(ProductParam)s ORDER BY {order_by};", 'new_schema', params)
        elif company:
            dataFrame = toDataframe(f"SELECT o.Product_Name, o.catalog_num ,o.Company_Name, o.Unit_Price, s.Quantity FROM  stock_info S left join Order_Info O on S.Product_Num = O.Product_Num WHERE Company_Name COLLATE utf8mb4_general_ci LIKE %(CompanyParam)s ORDER BY {order_by};", 'new_schema', params)
        elif product:
            dataFrame = toDataframe(f"SELECT o.Product_Name, o.catalog_num ,o.Company_Name, o.Unit_Price, s.Quantity FROM  stock_info S left join Order_Info O on S.Product_Num = O.Product_Num WHERE Product_Name COLLATE utf8mb4_general_ci LIKE %(ProductParam)s ORDER BY {order_by};", 'new_schema', params)
        elif sort == "QuantityDescending":
            dataFrame = toDataframe(f"SELECT o.Product_Name, o.catalog_num ,o.Company_Name, o.Unit_Price, s.Quantity FROM  stock_info S left join Order_Info O on S.Product_Num = O.Product_Num ORDER BY Quantity DESC;", 'new_schema')
        else: # Default if all fields are empty or sort
            dataFrame = toDataframe(f"SELECT o.Product_Name, o.catalog_num ,o.Company_Name, o.Unit_Price, s.Quantity FROM  stock_info S left join Order_Info O on S.Product_Num = O.Product_Num ORDER BY {order_by};", 'new_schema')
        
        # renaming columns and setting data variable
        dataFrame.rename(columns={'Product_Name': 'Product', 'catalog_num': 'Catalog Number','Company_Name': 'Company Name', 'Unit_Price': 'Cost'}, inplace=True)
        data = dataFrame.to_dict('records')

    if request.method == 'GET':
        dataFrame = toDataframe("SELECT o.Product_Name, o.catalog_num ,o.Company_Name, o.Unit_Price, s.Quantity FROM  stock_info S left join Order_Info O on S.Product_Num = O.Product_Num ORDER BY Quantity;", 'new_schema')
        dataFrame.rename(columns={'Product_Name': 'Product', 'catalog_num': 'Catalog Number','Company_Name': 'Company Name', 'Unit_Price': 'Cost'}, inplace=True)
        data = dataFrame.to_dict('records')

    try:
        # use to prevent user from caching pages
        response = make_response(render_template("stock.html", data=data, list=list, len=len, str=str))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    except UndefinedError:
        print("jinja2.exceptions.UndefinedError: list object has no element 0")
        
        dataFrame = toDataframe("SELECT o.Product_Name, o.catalog_num ,o.Company_Name, o.Unit_Price, s.Quantity FROM  stock_info S left join Order_Info O on S.Product_Num = O.Product_Num ORDER BY Quantity;", 'new_schema')
        dataFrame.rename(columns={'Product_Name': 'Product', 'catalog_num': 'Catalog Number','Company_Name': 'Company Name', 'Unit_Price': 'Cost'}, inplace=True)
        data = dataFrame.to_dict('records')
        # use to prevent user from caching pages
        response = make_response(render_template("stock.html", data=data, list=list, len=len, str=str))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response