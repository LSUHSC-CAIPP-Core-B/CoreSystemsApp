from flask import render_template, request, redirect, url_for, flash, make_response
from flask_paginate import Pagination, get_page_args
from app.CoreC.stock import bp
from app.reader import Reader
from app import login_required
import mysql.connector as connection
import pandas as pd

def toDictionary(query, database_name):
    try:
        mydb = connection.connect(host="127.0.0.1", database = database_name,user="root", passwd="FrdL#7329",use_pure=True, auth_plugin='mysql_native_password')
        result_dataFrame = pd.read_sql(query,mydb)
        mydb.close() #close the connection
        return result_dataFrame.to_dict('records')
    except Exception as e:
        print(str(e))
        mydb.close()

#information_reader = Reader("PI_ID - PI_ID.csv")

@bp.route('/stock', methods=['GET'])
@login_required(role=["user", "coreC"])
def stock():
    if request.method == 'GET':
        data = toDictionary("SELECT o.Product_Name, o.Company_Name, s.Quantity FROM  stock_info S left join Order_Info O on S.Product_Num = O.Product_Num;", 'new_schema')

        # use to prevent user from caching pages
        response = make_response(render_template("stock.html", data=data, list=list, len=len, str=str))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    
@bp.route('/antibodies', methods=['GET'])
@login_required(role=["user", "coreC"])
def antibodies_route():
    if request.method == 'GET':
        data = toDictionary("SELECT Box_name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost FROM Antibodies_Stock;", 'antibodies')

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
        data = toDictionary("SELECT * FROM panels", 'antibodies')

        # use to prevent user from caching pages
        response = make_response(render_template("panels.html", data=data, list=list, len=len, str=str))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response