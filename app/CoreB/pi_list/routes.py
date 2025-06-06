from flask import Flask, render_template, request, redirect, url_for, flash, make_response, send_from_directory
from flask_paginate import Pagination, get_page_args
import pandas as pd
from app.CoreB.pi_list import bp
from app.reader import Reader, find
from app import login_required
from app.utils.db_utils import db_utils
from app.CoreB.pi_list.pi_table import PI_table
from flask_caching import Cache

information_reader = Reader("PI_ID - PI_ID.csv")

app = Flask(__name__)
cache1 = Cache(app, config={'CACHE_TYPE': 'simple'}) # Memory-based cache
defaultCache = Cache(app, config={'CACHE_TYPE': 'simple'})

PI_table = PI_table()

@bp.route('/information', methods=['GET'])
@login_required(role=["admin", "coreB"])
def information():
    """
    GET: Show information on PI with specified ID
    """
    if request.method == 'GET':
        # get PI list data
        data = information_reader.getRawDataCSV(headers=True, dict=True)
        order_num = request.args.get('order_num').split("_")[0]

        # get specific PI data
        data = [dict for dict in data if dict['PI ID'].lower().__contains__(order_num.lower())]
        if len(data) == 0:
            flash('There is no PI with given ID in Project ID')
            return redirect(url_for('orders.orders'))
        else:
            pi_data = data[0]

        # use to prevent user from caching pages
        response = make_response(render_template('pi/information.html', data=pi_data, order_num=order_num, list=list, len=len, str=str))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

@bp.route('/pilist', methods=['GET', 'POST'])
@login_required(role=["admin", "coreB"])
def pilist():
    """
    GET: Display list of all PIs
    POST: Dispaly filtered list of all PIs
    """
    # get PI list data

    if request.method == 'GET':
        dataFrame = db_utils.toDataframe("Select * FROM pi_info;", 'app/Credentials/CoreB.json')
        data = dataFrame.to_dict('records')

    if request.method == 'POST':
        pi_name = request.form.get('PI full name')
        dept = request.form.get('Department')
        sort = request.form.get('sort')
        
        # Stores all possible Inputs
        AllUinputs = [pi_name, dept]
        
        # Creates list to store inputs that are being Used
        Uinputs: list[str] = [i for i in AllUinputs]

        # Clear the cache when new filters are applied
        with app.app_context():
            cache1.delete('cached_dataframe')

        data = PI_table.display(Uinputs, sort)

        with app.app_context():
            cache1.set('cached_dataframe', data, timeout=3600)  # Cache for 1 hour (3600 seconds)

    page, per_page, offset = get_page_args(page_parameter='page', 
                                        per_page_parameter='per_page')
    total = len(data)

    pagination_users = data[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=total)

    # use to prevent user from caching pages
    response = make_response(render_template('pi/pi_list.html', data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

@bp.route('/add_pi', methods=['GET', 'POST'])
@login_required(role=["admin", "coreB"])
def add_pi():
    """
    GET: Display screen to input new PI information
    POST: Add new PI with specified information
    """
    if request.method == 'GET':
        pi_data = {
            "PI_first_name": "",
            "PI_last_name": "",
            "PI_ID": "",
            "PI_email": "",
            "PI_departmnet": ""
        }
        # use to prevent user from caching pages
        response = make_response(render_template('pi/add_pi.html', fields = pi_data))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

    elif request.method == 'POST':
        first_name = request.form.get('PI_first_name')
        last_name = request.form.get('PI_last_name')
        pi_id = request.form.get('PI_ID').strip()
        email = request.form.get('PI_email')
        department = request.form.get('PI_departmnet')

        # fields cannot be empty
        if first_name == "" or last_name == "" or pi_id == "" or email == "" or department == "":
            flash('Fields cannot be empty')
            return redirect(url_for('pi_list.add_pi'))
        
        # get csv data
        data = information_reader.getRawDataCSV(headers=True, dict=True)

        # check if PI ID already exists
        for d in data:
            if pi_id == d["PI ID"]:
                flash('PI with this ID already exists, please pick a new one.')
                return redirect(url_for('pi_list.add_pi'))
            

        # new row
        row = {
            'PI full name':first_name + "_" + last_name,
            'PI ID':pi_id,
            'email':email,
            'Department':department
        }

        data.append(row)

        information_reader.saveRawDataCSV(data)
                
        # use to prevent user from caching pages
        response = make_response(redirect(url_for('pi_list.pilist')))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    
@bp.route('/delete_pi', methods=['GET'])
@login_required(role=["admin", "coreB"])
def delete_pi():
    """
    GET: Delete PI
    """
    if request.method == 'GET':
        # variable to hold CSV data
        data = information_reader.getRawDataCSV(headers=True, dict=False)
        pi_id = request.args.get('pi_id')
        data = data[data["PI ID"].str.contains(pi_id) == False]
        data_dict = data.to_dict()
        information_reader.saveRawDataCSV(data_dict)

        # use to prevent user from caching pages
        response = make_response(redirect(url_for('pi_list.pilist')))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

@bp.route('/update_pi', methods=['GET', 'POST'])
@login_required(role=["admin", "coreB"])
def update():
    """
    GET: Display edit screen of selected PI
    POST: Update selected PI data
    """
    if request.method == 'GET':
        old_pi_full_name = request.args.get('pi_id_old')
        query = "Select * FROM pi_info WHERE `PI full name` = %s"

        df = db_utils.toDataframe(query, 'app/Credentials/CoreB.json', params=(old_pi_full_name,))
        update_data = df.iloc[0]
        index = update_data['index']

        #Seperate first and last name
        name_array = update_data["PI full name"].split("_")
        update_data['PI first name'] = name_array[0]
        update_data['PI last name'] = name_array[1]

        #Remove full name column
        del update_data["PI full name"]

        #Change order to put first and last name in front
        column_order = ["PI first name", "PI last name", "PI ID", "email", "Department"]
        update_data = update_data[column_order]

        return render_template('pi/update_pi.html', fields = update_data, pi_id_old = old_pi_full_name, index=index)
  
    elif request.method == 'POST':
        params = request.form.to_dict()

        old_pi_full_name = request.args.get('pi_id_old')

        index = request.form.get('index')
        pi_query = "SELECT `PI ID` FROM pi_info WHERE `index` = %s"
        PI_id = db_utils.toDataframe(pi_query, 'app/Credentials/CoreB.json', params=(index,))

        query = "Select `PI ID` FROM pi_info"
        df = db_utils.toDataframe(query, 'app/Credentials/CoreB.json')
        
        # Check if the PI ID is available or taken
        for v in df['PI ID']:
            if v == request.form.get('PI ID') and v != PI_id.iat[0,0]:
                flash('PI with this ID already exists, please pick a new one.')
                return redirect(url_for('pi_list.update', pi_id_old = old_pi_full_name))
        

        #Reconstruct first and last name into full name
        fname = request.form.get('PI first name')
        lname = request.form.get('PI last name')
        full_name = "_".join([fname, lname])

        params.pop("PI first name")
        params.pop("PI last name")
        params['PI full name'] = full_name

        #replace spaces in the key names with underscores
        valid_params = {k.replace(" ", "_"): v for k, v in params.items()}

        PI_table.change(valid_params)

        # use to prevent user from caching pages
        response = make_response(redirect(url_for('pi_list.pilist')))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response