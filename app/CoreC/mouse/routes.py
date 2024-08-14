from io import BytesIO

import mysql.connector as connection
import pandas as pd
import pymysql
from app import login_required
from app.CoreC.mouse import bp
from app.CoreC.mouse.mouseTable import mouseTable
from app.utils.db_utils import db_utils
from app.utils.logging_utils.logGenerator import Logger
from flask import (Flask, flash, jsonify, make_response, redirect,
                   render_template, request, send_file, url_for)
from flask_caching import Cache
from flask_paginate import Pagination, get_page_args
from flask_login import current_user

mouseTable = mouseTable()

# Logging set up
logFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LogGenerator = Logger(logFormat=logFormat, logFile='application.log')
logger = LogGenerator.generateLogger()

@bp.route('/mouse', methods=['GET', 'POST'])
@login_required(role=["user", "coreC"])
def mouse():
    if request.method == 'POST':
        rawInputs = request.form

        inputDict = rawInputs.to_dict()
        print(inputDict)
        Uinputs = list(inputDict.values())

        sort = inputDict["sort"]

        Uinputs.pop(-1)

        data: dict = mouseTable.display(Uinputs, sort)
    
    if request.method == 'GET':
        df = db_utils.toDataframe("SELECT * FROM Mouse_Stock WHERE Genotype != 'N/A';", 'app/Credentials/CoreC.json')
        df.rename(columns={'PI_Name': 'PI', 'Mouse_Description': 'Description', 'Times_Back_Crossed': 'Times Back Crossed', 'MTA_Required': 'MTA Required'}, inplace=True)
        
        data = df.to_dict('records')

    page, per_page, offset = get_page_args(page_parameter='page', 
                                        per_page_parameter='per_page')

    if not current_user.is_admin:
        per_page = request.args.get('per_page', 20, type=int)
        offset = (page - 1) * per_page
    
    #number of rows in table
    num_rows = len(data)

    pagination_users = data[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=num_rows)
    
    # use to prevent user from caching pages
    response = make_response(render_template("CoreC/mouse_stock.html", data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str, num_rows=num_rows))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response
    
@bp.route('/addMouse', methods=['GET', 'POST'])
@login_required(role=["user", "coreC"])
def addMouse():
    if request.method == 'POST':
        inputs = request.form
        
        inputData = inputs.to_dict()

        has_empty_value = any(value == "" or value is None for value in inputData.values())
        
        if has_empty_value:
            flash('Fields cannot be empty')
            return redirect(url_for('mouse.addMouse'))
        
        if not inputData["Times Back Crossed"].isdigit():
            flash('"Times Back Crossed" must be a number')
            return redirect(url_for('mouse.addMouse'))

        df = mouseTable.add(inputData)
        df.rename(columns={'Box_Name': 'Box Name'}, inplace=True)
        data = df.to_dict(orient='records')
        
        page, per_page, offset = get_page_args(page_parameter='page', 
                                           per_page_parameter='per_page')
        
        #number of rows in table
        num_rows = len(data)

        pagination_users = data[offset: offset + per_page]
        pagination = Pagination(page=page, per_page=per_page, total=num_rows)
        
        # use to prevent user from caching pages
        response = make_response(render_template("CoreC/mouse_stock.html", data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str, num_rows=num_rows))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    
    if request.method == 'GET':
        data = {
            "PI": "",
            "Genotype": "",
            "Description": "",
            "Strain": "",
            "Times Back Crossed": "",
            "MTA Required": "",
        }

        # use to prevent user from caching pages
        response = make_response(render_template('CoreC/add_mouse.html', fields = data))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    
@bp.route('/deleteMouse', methods=['POST'])
@login_required(role=["user", "coreC"])
def deleteAntibody():
    primary_key = request.form['primaryKey']

    logger.info("Deletion Attempting...")

    mouseTable.delete(primary_key)

    # use to prevent user from caching pages
    response = make_response(redirect(url_for('mouse.mouse')))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response