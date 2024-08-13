import json
import re
from datetime import datetime
from io import BytesIO

import mysql.connector as connection
import pandas as pd
import pymysql
from app import login_required
from app.CoreC.stock import bp
from app.CoreC.stock.stockTable import stockTable
from app.reader import Reader
from app.utils.db_utils import db_utils
from app.utils.logging_utils.logGenerator import Logger
from app.utils.search_utils import search_utils
from flask import (Flask, flash, jsonify, make_response, redirect,
                   render_template, request, send_file, url_for)
from flask_caching import Cache
from flask_paginate import Pagination, get_page_args
from fuzzywuzzy import fuzz, process
from jinja2 import UndefinedError

app = Flask(__name__)

cache1 = Cache(app, config={'CACHE_TYPE': 'simple'})  # Memory-based cache
defaultCache = Cache(app, config={'CACHE_TYPE': 'simple'})

stockTable = stockTable()

# Logging set up
logFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LogGenerator = Logger(logFormat=logFormat, logFile='application.log')
logger = LogGenerator.generateLogger()

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
        Uinputs: list[str] = [i for i in AllUinputs]

        # Clear the cache when new filters are applied
        with app.app_context():
            cache1.delete('cached_dataframe')

        data: dict = stockTable.display(Uinputs, sort)
        with app.app_context():
            cache1.set('cached_dataframe2', data, timeout=3600)

    if request.method == 'GET':
        with app.app_context():
            cached_data = cache1.get('cached_dataframe2')
        if cached_data is None:
            with app.app_context():
                defaultCache.delete('cached_dataframe')

            dataFrame = db_utils.toDataframe("SELECT S.Product_Num, O.Product_Name, O.Catalog_Num , O.Company_Name, O.Unit_Price, S.Quantity FROM  Stock_Info S left join Order_Info O on S.Product_Num = O.Product_Num WHERE O.Company_Name != 'N/A' AND O.Product_Name != '0' ORDER BY Quantity;", 'app/Credentials/CoreC.json')
            dataFrame.rename(columns={'Product_Name': 'Product', 'Catalog_Num': 'Catalog Number','Company_Name': 'Company Name', 'Unit_Price': 'Cost'}, inplace=True)
            data = dataFrame.to_dict('records')

            with app.app_context():
                defaultCache.set('cached_dataframe', data, timeout=3600)
        else:
            with app.app_context():
                data = cache1.get('cached_dataframe2')
    
    page, per_page, offset = get_page_args(page_parameter='page', 
                                           per_page_parameter='per_page')
    #number of rows in table
    num_rows = len(data)

    pagination_users = data[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=num_rows)

    # use to prevent user from caching pages
    response = make_response(render_template("CoreC/stock.html", data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str, num_rows=num_rows))
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
    Uinputs: list[str] = [i for i in AllUinputs if i]

    
    # Maps sorting options to their corresponding SQL names
    sort_orders = {
        'Product': 'Product_Name',
        'Cost': 'Unit_Price'
    }
    return stockTable.display(Uinputs, sort, sort_orders)

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

        if not Quantity.isdigit():
            flash('Titration must be a number')
            return redirect(url_for('stock.addSupply'))
        
        try:
            float(cost)
        except ValueError:
            flash('Cost must be a number')
            return redirect(url_for('stock.addSupply'))

        params = {'CompanyParam': Company_Name, 
                    'catalogNumParam': catalog_num , 
                    'costParam': cost,
                    'ProductParam': Product_Name
                    }

        stockTable.add(params, Quantity)

        # use to prevent user from caching pages
        response = make_response(redirect(url_for('stock.stock')))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

    if request.method == 'GET':
        data = {
            "Company Name": "",
            "Catalog Number": "",
            "Cost": "",
            "Product Name": "",
            "Quantity": "",
        }

        # use to prevent user from caching pages
        response = make_response(render_template('CoreC/add_supply.html', fields = data))
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

        # Making sure catalog number field isnt empty
        if catalog_num == "" or catalog_num.lower() == "n/a":
            flash('Fields cannot be empty')
            return redirect(url_for('stock.addSupply'))

        if not Quantity.isdigit():
            flash('Titration must be a number')
            return redirect(url_for('stock.addSupply'))
        
        try:
            float(cost)
        except ValueError:
            flash('Cost must be a number')
            return redirect(url_for('stock.addSupply'))

        params = {'CompanyParam': Company_Name, 
                      'catalogNumParam': catalog_num , 
                      'costParam': cost,
                      'ProductParam': Product_Name,
                      'Pkey': primary_key
                      }

        stockTable.change(params, Quantity, primary_key)

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
        response = make_response(render_template('CoreC/change_supply.html', fields = data, pkey = primary_key))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    
@bp.route('/deleteSupply', methods=['POST'])
@login_required(role=["admin"])
def deleteSupply():
    primary_key = request.form['primaryKey']

    logger.info("Deletion Attempting...")

    stockTable.delete(primary_key)

    # use to prevent user from caching pages
    response = make_response(redirect(url_for('stock.stock')))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

@bp.route('/downloadStockCSV', methods=['GET'])
@login_required(role=["coreC"])
def downloadCSV():
    with app.app_context():
        saved_data = cache1.get('cached_dataframe2')
    
    if saved_data is None:
        with app.app_context():
            saved_data = defaultCache.get('cached_dataframe')

    df = pd.DataFrame.from_dict(saved_data)
    csv = df.to_csv(index=False)
    
    # Convert the CSV string to bytes and use BytesIO
    csv_bytes = csv.encode('utf-8')
    csv_io = BytesIO(csv_bytes)
    
    return send_file(csv_io, mimetype='text/csv', as_attachment=True, download_name='Stock.csv')