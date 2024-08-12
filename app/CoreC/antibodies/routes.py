from datetime import datetime
from io import BytesIO

import mysql.connector as connection
import pandas as pd
import pymysql
from app import login_required
from app.CoreC.antibodies import bp
from app.CoreC.antibodies.antibodiesTable import antibodiesTable
from app.reader import Reader
from app.utils.db_utils import db_utils
from app.utils.logging_utils.logGenerator import Logger
from app.utils.search_utils import search_utils
from flask import (Flask, flash, jsonify, make_response, redirect,
                   render_template, request, send_file, url_for)
from flask_caching import Cache
from flask_paginate import Pagination, get_page_args
from flask_login import current_user
from fuzzywuzzy import fuzz
from jinja2 import UndefinedError

app = Flask(__name__)
cache1 = Cache(app, config={'CACHE_TYPE': 'simple'}) # Memory-based cache
defaultCache = Cache(app, config={'CACHE_TYPE': 'simple'})

antibodiesTable = antibodiesTable()

# Logging set up
logFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LogGenerator = Logger(logFormat=logFormat, logFile='application.log')
logger = LogGenerator.generateLogger()

@bp.route('/antibodies', methods=['GET', 'POST'])
@login_required(role=["user", "coreC"])
def antibodies():
    if request.method == 'POST':
        Company_name = request.form.get('company_name') or ""
        Target_Name = request.form.get('target_name') or ""
        Target_Species = request.form.get('target_species') or ""
        sort = request.form.get('sort') or 'Original'

        # Stores all possible Inputs
        AllUinputs = [Company_name, Target_Name, Target_Species]
        
        # Creates list to store inputs that are being Used
        Uinputs: list[str] = [i for i in AllUinputs]
        
        # Clear the cache when new filters are applied
        with app.app_context():
            cache1.delete('cached_dataframe')

        data: dict = antibodiesTable.display(Uinputs, sort)
        with app.app_context():
            cache1.set('cached_dataframe', data, timeout=3600)  # Cache for 1 hour (3600 seconds)
            
    if request.method == 'GET':
        with app.app_context():
            cached_data = cache1.get('cached_dataframe')
        if cached_data is None:
            with app.app_context():
                defaultCache.delete('cached_dataframe')

            if current_user.is_admin:
                dataFrame = db_utils.toDataframe("SELECT Stock_ID, Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, DATE_FORMAT(Expiration_Date, '%m/%d/%Y') AS Expiration_Date, Titration, Cost FROM Antibodies_Stock WHERE Included = 1 ORDER BY Target_Name;", 'app/Credentials/CoreC.json')
                dataFrame.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
            else:
                dataFrame = db_utils.toDataframe("SELECT Stock_ID, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype FROM Antibodies_Stock WHERE Included = 1 ORDER BY Target_Name;", 'app/Credentials/CoreC.json')
                dataFrame.rename(columns={'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone'}, inplace=True)
            data = dataFrame.to_dict('records')

            with app.app_context():
                defaultCache.set('cached_dataframe', data, timeout=3600)
        else:
            # Try to get the cached DataFrame
            with app.app_context():
                data = cache1.get('cached_dataframe')

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
    response = make_response(render_template("CoreC/antibodies_stock.html", data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str, num_rows=num_rows))
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
            return redirect(url_for('antibodies.addAntibody'))

        if db_utils.isValidDateFormat(expiration_date):
            if not db_utils.isValidDate(expiration_date):
                flash('Not a valid Date')
                return redirect(url_for('antibodies.addAntibody'))
        else:
            flash('Date must be in "YYYY-MM-DD" format')
            return redirect(url_for('antibodies.addAntibody'))
        
        if not titration.isdigit():
            flash('Titration must be a number')
            return redirect(url_for('antibodies.addAntibody'))
        
        try:
            float(cost)
        except ValueError:
            flash('Cost must be a number')
            return redirect(url_for('antibodies.addAntibody'))

        if not (included := antibodiesTable.isIncludedValidInput(included)):
            return redirect(url_for('antibodies.addAntibody'))

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

        # Executes add query
        df = antibodiesTable.add(params)
        df.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
        data = df.to_dict(orient='records')
        
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
        response = make_response(render_template("CoreC/antibodies_stock.html", data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str, num_rows=num_rows))
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
            "Cost": "",
            "Included": ""
        }

        # use to prevent user from caching pages
        response = make_response(render_template('CoreC/add_antibody.html', fields = data))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

@bp.route('/deleteAntibody', methods=['POST'])
@login_required(role=["admin"])
def deleteAntibody():
    primary_key = request.form['primaryKey']

    logger.info("Deletion Attempting...")

    antibodiesTable.delete(primary_key)

    # use to prevent user from caching pages
    response = make_response(redirect(url_for('antibodies.antibodies')))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

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
            return redirect(url_for('antibodies.changeAntibody'))

        if db_utils.isValidDateFormat(expiration_date):
            if not db_utils.isValidDate(expiration_date):
                flash('Not a valid Date')
                return redirect(url_for('antibodies.changeAntibody'))
        else:
            flash('Date must be in "YYYY-MM-DD" format')
            return redirect(url_for('antibodies.changeAntibody'))

        if not titration.isdigit():
            flash('Titration must be a number')
            return redirect(url_for('antibodies.addAntibody'))
        
        try:
            float(cost)
        except ValueError:
            flash('Cost must be a number')
            return redirect(url_for('antibodies.addAntibody'))

        if not (included := antibodiesTable.isIncludedValidInput(included)):
            return redirect(url_for('antibodies.addAntibody'))

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

        #Executes change query
        antibodiesTable.change(params)

        # use to prevent user from caching pages
        response = make_response(redirect(url_for('antibodies.antibodies')))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

    if request.method == 'GET':
        primary_key = request.args.get('primaryKey')
        query = "SELECT Box_Name, Company_name, Catalog_Num, Target_Name, Target_Species, Fluorophore, Clone_Name, Isotype, Size, Concentration, Expiration_Date, Titration, Cost, Included FROM Antibodies_Stock WHERE Stock_ID = %s;"
        df = db_utils.toDataframe(query, 'app/Credentials/CoreC.json', (primary_key,))
        df.rename(columns={'Box_Name': 'Box Name', 'Company_name': 'Company', 'Catalog_Num': 'Catalog Number', 'Target_Name': 'Target', 'Target_Species': 'Target Species', 'Clone_Name': 'Clone', 'Expiration_Date': 'Expiration Date', 'Cost': 'Cost ($)'}, inplace=True)
        
        # Converts 1 to yes and 0 to no from the included column
        if df.iloc[0,13] == 1:
            df.iloc[0,13] = "Yes"
        else:
            df.iloc[0,13] == "No"

        data = df.to_dict()
        
        # use to prevent user from caching pages
        response = make_response(render_template('CoreC/change_antibody.html', fields = data, pkey = primary_key))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

@bp.route('/downloadAntibodyCSV', methods=['GET'])
@login_required(role=["coreC"])
def downloadCSV():
    with app.app_context():
        saved_data = cache1.get('cached_dataframe')
    
    if saved_data is None:
        with app.app_context():
            saved_data = defaultCache.get('cached_dataframe')

    csv_io = antibodiesTable.download_CSV(saved_data=saved_data)
    
    return send_file(csv_io, mimetype='text/csv', as_attachment=True, download_name='Antibodies.csv')