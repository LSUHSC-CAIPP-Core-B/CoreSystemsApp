from flask import render_template, request, redirect, url_for, flash, make_response
from flask_paginate import Pagination, get_page_args
from jinja2 import UndefinedError
from app.CoreC.stock import bp
from app.reader import Reader
from app import login_required
import mysql.connector as connection
import pandas as pd

def toDataframe(query, database_name, params=None):
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
            'Expiration Date': 'Expiration_Date'
        }
        # Check if sort is in the dictionary, if not then uses default value
        order_by = sort_orders.get(sort, 'Target_Name')

        # Validate and sanitize the order_by to prevent sql injection
        if order_by not in sort_orders.values():
            order_by = 'Target_Name'  # Set a default value or handle the error
        
        # Dictionary of Parameters
        params = {'CompanyParam': company_name, 'TargetParam': target_name, 'TargerSpeciesParam': target_species}
        
        if company_name and target_name and target_species:
            dataFrame = toDataframe(f"SELECT Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 AND Company_name = %(CompanyParam)s AND (Target_Name = %(TargetParam)s OR Target_Name REGEXP CONCAT('^', %(TargetParam)s, '[a-f]')) AND Target_Species = %(TargerSpeciesParam)s ORDER BY {order_by};", 'antibodies', params)
            dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date'}, inplace=True)
            data = dataFrame.to_dict('records')
        elif company_name and target_name:
            dataFrame = toDataframe(f"SELECT Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 AND Company_name = %(CompanyParam)s AND (Target_Name = %(TargetParam)s OR Target_Name REGEXP CONCAT('^', %(TargetParam)s, '[a-f]')) ORDER BY {order_by};", 'antibodies', params)
            dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date'}, inplace=True)
            data = dataFrame.to_dict('records')
        elif company_name and target_species:
            dataFrame = toDataframe(f"SELECT Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 AND Company_name = %(CompanyParam)s AND Target_Species = %(TargerSpeciesParam)s ORDER BY {order_by};", 'antibodies', params)
            dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date'}, inplace=True)
            data = dataFrame.to_dict('records')
        elif target_name and target_species:
            dataFrame = toDataframe(f"SELECT Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 AND (Target_Name = %(TargetParam)s OR Target_Name REGEXP CONCAT('^', %(TargetParam)s, '[a-f]')) AND Target_Species = %(TargerSpeciesParam)s ORDER BY {order_by};", 'antibodies', params)
            dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date'}, inplace=True)
            data = dataFrame.to_dict('records')
        # Checks if value is given
        elif company_name:
            param = (company_name,)
            dataFrame = toDataframe(f"SELECT Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 AND Company_name = %s ORDER BY {order_by};", 'antibodies', param)
            dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date'}, inplace=True)
            data = dataFrame.to_dict('records')
        elif target_name:
            param = (target_name,)
            dataFrame = toDataframe(f"SELECT Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 AND (Target_Name = %(TargetParam)s OR Target_Name REGEXP CONCAT('^', %(TargetParam)s, '[a-f]')) ORDER BY {order_by};", 'antibodies', params)
            dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date'}, inplace=True)
            data = dataFrame.to_dict('records')
        elif target_species:
            param = (target_species,)
            dataFrame = toDataframe(f"SELECT Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 AND Target_Species = %s ORDER BY {order_by};", 'antibodies', param)
            dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date'}, inplace=True)
            data = dataFrame.to_dict('records')
        elif sort:
            dataFrame = toDataframe(f"SELECT Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 ORDER BY {order_by};", 'antibodies')
            dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date'}, inplace=True)
            data = dataFrame.to_dict('records')
        else:
            # When fields are empty
            dataFrame = toDataframe("SELECT Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 ORDER BY Target_Name;", 'antibodies')
            dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date'}, inplace=True)
            data = dataFrame.to_dict('records')

    if request.method == 'GET':
        dataFrame = toDataframe("SELECT Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 ORDER BY Target_Name;", 'antibodies')
        dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date'}, inplace=True)
        data = dataFrame.to_dict('records')
    
    try:
        # use to prevent user from caching pages
        response = make_response(render_template("antibodies_stock.html", data=data, list=list, len=len, str=str))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    except UndefinedError:
        print("jinja2.exceptions.UndefinedError: list object has no element 0")
        
        dataFrame = toDataframe("SELECT Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 0 AND Catalog_Num = 0;", 'antibodies')
        dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date'}, inplace=True)
        data = dataFrame.to_dict('records')
        # use to prevent user from caching pages
        response = make_response(render_template("antibodies_stock.html", data=data, list=list, len=len, str=str))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

@bp.route('/panels', methods=['GET'])
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
    
@bp.route('/addAntibody', methods=['GET', 'POST'])
@login_required(role=["user", "coreC"])
def addAntibody():
    if request.method == 'POST':
        return render_template('add_antibody.html')

    if request.method == 'GET':
        return render_template('add_antibody.html')

@bp.route('/stock', methods=['GET'])
@login_required(role=["admin", "coreC"])
def stock():
    if request.method == 'GET':
        dataFrame = toDataframe("SELECT o.Product_Name, o.catlog_num ,o.Company_Name, s.Quantity FROM  stock_info S left join Order_Info O on S.Product_Num = O.Product_Num;", 'new_schema')
        dataFrame.rename(columns={'Product_Name': 'Product', 'Catlog_Num': 'Catalog Number','Company_Name': 'Company Name'}, inplace=True)
        data = dataFrame.to_dict('records')

        # use to prevent user from caching pages
        response = make_response(render_template("stock.html", data=data, list=list, len=len, str=str))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response