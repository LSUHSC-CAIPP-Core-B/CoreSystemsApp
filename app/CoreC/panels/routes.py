from datetime import datetime
from io import BytesIO

import mysql.connector as connection
import pandas as pd
import pymysql
from app import login_required
from app.CoreC.panels import bp
from app.utils.db_utils import db_utils
from app.utils.search_utils import search_utils
from flask import (Flask, flash, jsonify, make_response, redirect,
                   render_template, request, send_file, url_for)
from flask_caching import Cache
from flask_paginate import Pagination, get_page_args
from fuzzywuzzy import fuzz
from flask_login import current_user

app = Flask(__name__)
cache1 = Cache(app, config={'CACHE_TYPE': 'simple'}) # Memory-based cache


@bp.route('/panels', methods=['GET', 'POST'])
@login_required(role=["user", "coreC"])
def panels():
    if request.method == 'POST':
        sort = request.form.get('sort') or 'Original'

        dataFrame = count_rows()

        if sort == "Number of Antibodies":
            dataFrame = dataFrame.sort_values(by='antibody_num', ascending=True)

        dataFrame.rename(columns={'Panel_Name': 'Panel', 'antibody_num': 'Number of Antibodies'}, inplace=True)
        data = dataFrame.to_dict('records')
    if request.method == 'GET':
        dataFrame = count_rows()
        dataFrame.rename(columns={'Panel_Name': 'Panel', 'antibody_num': 'Number of Antibodies'}, inplace=True)
        data = dataFrame.to_dict('records')
        
        panels_df = db_utils.toDataframe("SELECT Panel_name, Panel_table_name from predefined_panels;", 'app/Credentials/CoreC.json')
        with app.app_context():
            cache1.set('cached_dataframe', panels_df, timeout=604_800)

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

def count_rows() -> pd.DataFrame:
    # Fetches the panel names and table names
    panels_query = "SELECT Panel_name, Panel_table_name FROM predefined_panels"
    panels_df = db_utils.toDataframe(panels_query, 'app/Credentials/CoreC.json')
    
    # List to hold the results
    results = []
    
    # Iterates through each row in the DataFrame
    for index, row in panels_df.iterrows():
        panel_name = row['Panel_name']
        table_name = row['Panel_table_name']
        
        # Constructs the COUNT query
        count_query = f"SELECT COUNT(*) as antibody_num FROM {table_name}"
        count_df = db_utils.toDataframe(count_query, 'app/Credentials/CoreC.json')
        count = count_df['antibody_num'].iloc[0]
        
        # Appends the result to the list
        results.append({'Panel_name': panel_name, 'antibody_num': count})
    
    # Converts the results to a DataFrame
    results_df = pd.DataFrame(results)
    return results_df

@bp.route('/panel_details', methods=['GET', 'POST'])
@login_required(role=["user", "coreC"])
def panel_details():
    panel_name = request.args.get('Panel_Name')
    if request.method == 'POST':
        raise NotImplementedError()
    if request.method == 'GET':
        with app.app_context():
            panels_df = cache1.get('cached_dataframe')
        
        # Searches for the existing panel
        columns = [col for col in panels_df.columns if col]
        table_name_dict = search_utils.search_data([panel_name], columns_to_check=columns, threshold=90, SqlData=panels_df)
        table_name = pd.DataFrame(table_name_dict)
        
        # If not a panel was found then it gets the sql name of the panel
        if not table_name.empty:
            names = table_name.iloc[0]['Panel_table_name']

        # Checks permissions for data display
        if current_user.is_admin:
            dataFrame = db_utils.toDataframe(f"SELECT a.Stock_ID, a.Box_Name, a.Company_name, a.Catalog_Num, a.Target_Name, a.Target_Species, a.Fluorophore, a.Clone_Name, a.Isotype, a.Size, a.Concentration, DATE_FORMAT(a.Expiration_Date, '%m/%d/%Y') AS Expiration_Date,  a.Titration,  a.Cost FROM antibodies_stock a JOIN {names} m ON a.Stock_ID = m.stock_id WHERE a.Included = 1 ORDER BY a.Target_Name;", 'app/Credentials/CoreC.json')
            dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
        else:
            dataFrame = db_utils.toDataframe(f"SELECT a.Stock_ID, a.Company_name, a.Catalog_Num, a.Target_Name, a.Target_Species, a.Fluorophore, a.Clone_Name, a.Isotype FROM antibodies_stock a JOIN {names} m ON a.Stock_ID = m.stock_id WHERE a.Included = 1 ORDER BY a.Target_Name;", 'app/Credentials/CoreC.json')
            dataFrame.rename(columns={'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone'}, inplace=True)
        data = dataFrame.to_dict('records')

        if not data:
            flash('Panel is empty')
            return redirect(url_for('panels.panels'))

    page, per_page, offset = get_page_args(page_parameter='page', 
                                        per_page_parameter='per_page')
    
    per_page = request.args.get('per_page', 20, type=int)
    offset = (page - 1) * per_page


    #number of rows in table
    num_rows = len(data)

    pagination_users = data[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=num_rows)
    
    # use to prevent user from caching pages
    response = make_response(render_template("panel_details.html", Panel_Name=panel_name, data=pagination_users, pagination=pagination, list=list, len=len, str=str, num_rows=num_rows))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response