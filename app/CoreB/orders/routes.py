from flask import Flask, render_template, request, redirect, send_file, url_for, make_response, session
from flask_paginate import Pagination, get_page_args
import pandas as pd
import pymysql
from app import login_required
from app.CoreB.orders import bp
from flask_caching import Cache
from app.utils.db_utils import db_utils
from app.CoreB.orders.ordersTable import ordersTable

app = Flask(__name__)
cache1 = Cache(app, config={'CACHE_TYPE': 'simple'}) # Memory-based cache
defaultCache = Cache(app, config={'CACHE_TYPE': 'simple'})

ordersTable = ordersTable()

@bp.route('/orders', methods=['GET', 'POST'])
@login_required(role=["user", "coreB"])
def orders():
    """
    GET: Display list of all orders made
    POST: Display filtered list of all orders made
    """
    data = []
    if request.method == 'POST':
        # Store filters in session to be used in Update function
        session['filters'] = {
            'service_type': request.form.get('service_type') or "",
            'pi_name': request.form.get('pi_name') or "",
            'project_id': request.form.get('project_id') or "",
            'sort': request.form.get('sort') or "Original"
        }
        
        # Create list to store inputs that are being Used
        filters = session['filters']
        Uinputs = [filters['pi_name'], filters['project_id']]
        
        # Clear the cache when new filters are applied
        with app.app_context():
            cache1.delete('cached_dataframe')

        # Create dataframe with filters to display
        data = ordersTable.display(Uinputs, filters['sort'], filters['service_type'])

        with app.app_context():
            cache1.set('cached_dataframe', data, timeout=3600)  # Cache for 1 hour (3600 seconds)

    if request.method == 'GET':
        with app.app_context():
            cached_data = cache1.get('cached_dataframe')
        
        if cached_data is None:
            with app.app_context():
                defaultCache.delete('cached_dataframe')
            
            dataFrame = db_utils.toDataframe("Select * FROM CoreB_Order;", 'db_config/CoreB.json')
            data = dataFrame.to_dict('records')
            
            with app.app_context():
                defaultCache.set('cached_dataframe', data, timeout=3600)
        else:
            # Try to get cached Dataframe
            with app.app_context():
                data = cache1.get('cached_dataframe')

    page = request.args.get('page', 1, type=int)
    page, per_page, offset = get_page_args(page_parameter='page', 
                                           per_page_parameter='per_page')
    total = len(data)

    pagination_users = data[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=total)

    # use to prevent user from caching pages
    response = make_response(render_template('CoreB/orders.html', data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

@bp.route('/update', methods=['GET', 'POST'])
@login_required(role=["admin", "coreB"])
def update():
    """
    GET: Display edit screen of specified order
    POST: Update values of specified order
    """
    if request.method == "GET":
        question_id = request.args.get('question_id')
        query = "Select * FROM CoreB_Order WHERE `Index` = %s;"
        df = db_utils.toDataframe(query, 'db_config/CoreB.json', params=(question_id,))

        update_data = df.iloc[0]

        return render_template('CoreB/update.html', fields = update_data)
    
    elif request.method == "POST":
        params = request.form.to_dict()
        
        #replace spaces in the key names with underscores
        valid_params = {k.replace(" ", "_"): v for k, v in params.items()}

        # SQL Change query
        query = """UPDATE CoreB_Order SET `Project ID` = %(Project_ID)s,
            `Responsible Person` = %(Responsible_Person)s,
            `Complete status` = %(Complete_status)s,
            `Bill` = %(Bill)s,
            `Paid` = %(Paid)s,
            `Authoship Disclosure Agreement` = %(Authoship_Disclosure_Agreement)s,
            `Request Date` = %(Request_Date)s,
            `If it is an existing project` = %(If_it_is_an_existing_project)s,
            `PI Name` = %(PI_Name)s, 
            `Funding Source` = %(Funding_Source)s,
            `Account number and billing contact person` = %(Account_number_and_billing_contact_person)s, 
            `Project title` = %(Project_title)s, 
            `Project Description` = %(Project_Description)s, 
            `Service Type` = %(Service_Type)s, 
            `RNA Analysis Service Type` = %(RNA_Analysis_Service_Type)s, 
            `DNA Analysis Service Type` = %(DNA_Analysis_Service_Type)s, 
            `Protein Analysis Service Type` = %(Protein_Analysis_Service_Type)s, 
            `Metabolite Analysis Service Type` = %(Metabolite_Analysis_Service_Type)s, 
            `Organism and Species` = %(Organism_and_Species)s, 
            `Data Type` = %(Data_Type)s, 
            `Library Preparation` = %(Library_Preparation)s, 
            `Expected sample#` = %(Expected_sample#)s, 
            `Please list all comparisons` = %(Please_list_all_comparisons)s, 
            `Expected Completion Time`= %(Expected_Completion_Time)s, 
            `Questions and Special Requirments` = %(Questions_and_Special_Requirments)s  
            WHERE `Index` = %(Index)s;"""
        db_utils.execute(query, 'db_config/CoreB.json', params=valid_params)

        # Retrieve previously stored filters
        filters = session.get('filters', {
            'service_type': "",
            'pi_name': "",
            'project_id': "",
            'sort': "Original"
        })

        Uinputs = [filters['pi_name'],filters['project_id']]

        # Clear the cache when new filters are applied
        with app.app_context():
            cache1.delete('cached_dataframe')

        # Rebuild dataframe with the same filters applied
        data = ordersTable.display(Uinputs, filters['sort'], filters['service_type'])

        with app.app_context():
            cache1.set('cached_dataframe', data, timeout=3600)  # Cache for 1 hour (3600 seconds)

        current_page = request.args.get('page', 1)

        return redirect(url_for('orders.orders', page=current_page))

@bp.route('/delete', methods=['GET'])
@login_required(role=["admin", "coreB"])
def delete():
    """
    GET: Delete order
    """
    Index = request.args.get('question_id')

    # SQL DELETE query
    query = "DELETE FROM CoreB_Order WHERE `Index` = %s"

    db_utils.execute(query, 'db_config/CoreB.json', params=(Index,))

    # Retrieve previously stored filters
    filters = session.get('filters', {
        'service_type': "",
        'pi_name': "",
        'project_id': "",
        'sort': "Original"
    })

    Uinputs = [filters['pi_name'],filters['project_id']]

    # Clear the cache when new filters are applied
    with app.app_context():
        cache1.delete('cached_dataframe')

    # Rebuild dataframe with the same filters applied
    data = ordersTable.display(Uinputs, filters['sort'], filters['service_type'])

    with app.app_context():
        cache1.set('cached_dataframe', data, timeout=3600)  # Cache for 1 hour (3600 seconds)

    current_page = request.args.get('page', 1)
    return redirect(url_for('orders.orders', page=current_page))

@bp.route('/downloadOrdersCSV', methods=['GET'])
@login_required(role=["coreB"])
def downloadCSV():
    with app.app_context():
        saved_data = cache1.get('cached_dataframe')
    
    if saved_data is None:
        with app.app_context():
            saved_data = defaultCache.get('cached_dataframe')

    csv_io = ordersTable.download_CSV(saved_data=saved_data)
    
    return send_file(csv_io, mimetype='text/csv', as_attachment=True, download_name='Orders.csv')