from flask import Flask, render_template, request, redirect, send_file, url_for, flash, make_response, send_from_directory
from flask_paginate import Pagination, get_page_args
import pandas as pd
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
        # search vars
        service_type = request.form.get('service_type') or ""
        pi_name = request.form.get('pi_name') or ""
        sort = request.form.get('sort') or "Original"

        # Stores all possible Inputs
        AllUinputs = [pi_name]
        
        # Creates list to store inputs that are being Used
        Uinputs: list[str] = [i for i in AllUinputs]
        
        # Clear the cache when new filters are applied
        with app.app_context():
            cache1.delete('cached_dataframe')

        data = ordersTable.display(Uinputs, sort, service_type)
        with app.app_context():
            cache1.set('cached_dataframe', data, timeout=3600)  # Cache for 1 hour (3600 seconds)

    if request.method == 'GET':
        with app.app_context():
            cached_data = cache1.get('cached_dataframe')
        
        if cached_data is None:
            with app.app_context():
                defaultCache.delete('cached_dataframe')
            
            dataFrame = db_utils.toDataframe("Select * FROM CoreB_Order;", 'app/Credentials/CoreB.json')
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
    raise NotImplementedError()

@bp.route('/delete', methods=['GET'])
@login_required(role=["admin", "coreB"])
def delete():
    """
    GET: Delete order
    """
    raise NotImplementedError()

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