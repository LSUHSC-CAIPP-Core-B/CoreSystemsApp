from datetime import datetime
from io import BytesIO

import mysql.connector as connection
import pandas as pd
import pymysql
from app import login_required
from app.CoreC.panels import bp
from app.CoreC.antibodies.antibodiesTable import antibodiesTable
from app.reader import Reader
from app.utils.db_utils import db_utils
from app.utils.logging_utils.logGenerator import Logger
from app.utils.search_utils import search_utils
from flask import (Flask, flash, jsonify, make_response, redirect,
                   render_template, request, send_file, url_for)
from flask_caching import Cache
from flask_paginate import Pagination, get_page_args
from fuzzywuzzy import fuzz
from jinja2 import UndefinedError


@bp.route('/panels', methods=['GET', 'POST'])
@login_required(role=["user", "coreC"])
def panels():
    if request.method == 'POST':
        raise NotImplementedError()
    if request.method == 'GET':
        print("get method")
        dataFrame = db_utils.toDataframe("SELECT Panel_Name, (select COUNT(*) from antibodies_stock a join monica_innate_panel m where a.Stock_ID = m.stock_id) as antibody_num FROM predefined_panels ;", 'app/Credentials/CoreC.json')
        dataFrame.rename(columns={'Panel_Name': 'Panel', 'antibody_num': 'Number of Antibodies'}, inplace=True)
        data = dataFrame.to_dict('records')
        print("data")

    page, per_page, offset = get_page_args(page_parameter='page', 
                                        per_page_parameter='per_page')
    #number of rows in table
    num_rows = len(data)

    pagination_users = data[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=num_rows)
    
    # use to prevent user from caching pages
    response = make_response(render_template("predefined_Antibody_Panels.html", data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str, num_rows=num_rows))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

@bp.route('/panel_details', methods=['GET', 'POST'])
@login_required(role=["user", "coreC"])
def panel_details():
    panel_name = request.args.get('Panel_Name')
    if request.method == 'POST':
        raise NotImplementedError()
    if request.method == 'GET':
        table_names = {'Monica Innate': 'monica_innate_panel',
               'Monica Adaptive': 'monica_adaptive_panel'}
        
        names = table_names.get(panel_name, 'Monica Innate')

        dataFrame = db_utils.toDataframe(f"SELECT a.Stock_ID, a.Box_Name, a.Company_name, a.Catalog_Num, a.Target_Name, a.Target_Species, a.Fluorophore, a.Clone_Name, a.Isotype, a.Size, a.Concentration, DATE_FORMAT(a.Expiration_Date, '%m/%d/%Y') AS Expiration_Date,  a.Titration,  a.Cost FROM antibodies_stock a JOIN {names} m ON a.Stock_ID = m.stock_id WHERE a.Included = 1 ORDER BY a.Target_Name;", 'app/Credentials/CoreC.json')
        dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
        data = dataFrame.to_dict('records')

    page, per_page, offset = get_page_args(page_parameter='page', 
                                        per_page_parameter='per_page')
    #number of rows in table
    num_rows = len(data)

    pagination_users = data[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=num_rows)
    
    # use to prevent user from caching pages
    response = make_response(render_template("panel_details.html", Panel_Name=panel_name, data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str, num_rows=num_rows))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response