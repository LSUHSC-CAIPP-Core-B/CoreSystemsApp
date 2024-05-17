from flask import Flask, render_template, request, redirect, url_for, flash, make_response, jsonify
from flask_paginate import Pagination, get_page_args
from jinja2 import UndefinedError
from app.CoreC.stock import bp
from app.reader import Reader
from app import login_required
import mysql.connector as connection
import pandas as pd
import json
from fuzzywuzzy import fuzz, process
import pymysql
import re
from datetime import datetime
from flask_caching import Cache

from app.utils.db_utils import db_utils
from app.utils.search_utils import search_utils

app = Flask(__name__)

cache2 = Cache(app, config={'CACHE_TYPE': 'simple'})  # Memory-based cache


@bp.route('/stock', methods=['GET', 'POST'])
@login_required(role=["admin"])
def stock():
    if request.method == 'POST':
        # Clear the cache when new filters are applied
        with app.app_context():
            cache2.delete('cached_dataframe')


        data = create_or_filter_StockDataframe()
        with app.app_context():
            cache2.set('cached_dataframe2', data, timeout=3600)

    if request.method == 'GET':
        with app.app_context():
            cached_data = cache2.get('cached_dataframe2')
        if cached_data is None:
            dataFrame = db_utils.toDataframe("SELECT S.Product_Num, O.Product_Name, O.Catalog_Num , O.Company_Name, O.Unit_Price, S.Quantity FROM  Stock_Info S left join Order_Info O on S.Product_Num = O.Product_Num WHERE O.Company_Name != 'N/A' ORDER BY Quantity;", 'app/Credentials/CoreC.json')
            dataFrame.rename(columns={'Product_Name': 'Product', 'Catalog_Num': 'Catalog Number','Company_Name': 'Company Name', 'Unit_Price': 'Cost'}, inplace=True)
            data = dataFrame.to_dict('records')
        else:
            with app.app_context():
                data = cache2.get('cached_dataframe2')
    
    page, per_page, offset = get_page_args(page_parameter='page', 
                                           per_page_parameter='per_page')
    #number of rows in table
    num_rows = len(data)

    pagination_users = data[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=num_rows)

    # use to prevent user from caching pages
    response = make_response(render_template("stock.html", data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str, num_rows=num_rows))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

def create_or_filter_StockDataframe():
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
        query = f"SELECT S.Product_Num, O.Product_Name, O.Catalog_Num , O.Company_Name, O.Unit_Price, S.Quantity FROM  Stock_Info S left join Order_Info O on S.Product_Num = O.Product_Num WHERE O.Company_Name != 'N/A' ORDER BY {order_by};"
    else:
        query = f"SELECT S.Product_Num, O.Product_Name, O.Catalog_Num , O.Company_Name, O.Unit_Price, S.Quantity FROM  Stock_Info S left join Order_Info O on S.Product_Num = O.Product_Num WHERE O.Company_Name != 'N/A' ORDER BY {order_by} DESC;"
    
    df = db_utils.toDataframe(query, 'app/Credentials/CoreC.json')
    SqlData = df
    
    # * Fuzzy Search *
    # Checks whether filters are being used
    # If filters are used then implements fuzzy matching
    if len(Uinputs) != 0:
        columns_to_check = ["Company_Name", "Product_Name"]
        data = search_utils.search_data(Uinputs, columns_to_check, 45, SqlData)
        
        # If no match is found displays empty row
        if not data:
            dataFrame = db_utils.toDataframe("SELECT S.Product_Num, O.Product_Name, O.Catalog_Num , O.Company_Name, O.Unit_Price, S.Quantity FROM  Stock_Info S left join Order_Info O on S.Product_Num = O.Product_Num WHERE O.Company_Name = 'N/A' ORDER BY Quantity;", 'app/Credentials/CoreC.json')
            dataFrame.rename(columns={'Product_Name': 'Product', 'Catalog_Num': 'Catalog Number','Company_Name': 'Company Name', 'Unit_Price': 'Cost'}, inplace=True)
            data = dataFrame.to_dict('records')
    else: # If no search filters are used
        # renaming columns and setting data variable
        SqlData.rename(columns={'Product_Name': 'Product', 'Catalog_Num': 'Catalog Number','Company_Name': 'Company Name', 'Unit_Price': 'Cost'}, inplace=True)
        # Converts to a list of dictionaries
        data = SqlData.to_dict(orient='records')
    return data

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
            mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreC.json'))
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
        
        mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreC.json'))
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
        df = db_utils.toDataframe(query, 'app/Credentials/CoreC.json', (primary_key,))
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
        mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreC.json'))
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
