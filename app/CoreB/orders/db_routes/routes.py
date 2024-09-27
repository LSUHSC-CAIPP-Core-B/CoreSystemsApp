from flask import Flask, render_template, request, redirect, send_file, url_for, flash, make_response, send_from_directory
from flask_paginate import Pagination, get_page_args
import pandas as pd
from app import login_required
from app.CoreB.orders.db_routes import bp
from flask_caching import Cache
from app.utils.db_utils import db_utils

app = Flask(__name__)
cache1 = Cache(app, config={'CACHE_TYPE': 'simple'}) # Memory-based cache
defaultCache = Cache(app, config={'CACHE_TYPE': 'simple'})

@bp.route('/orders', methods=['GET', 'POST'])
@login_required(role=["user", "coreB"])
def orders():
    """
    GET: Display list of all orders made
    POST: Display filtered list of all orders made
    """
    if request.method == 'POST':
        pass

    if request.method == 'GET':
        with app.app_context():
            cached_data = cache1.get('cached_dataframe')
        
        if cached_data is None:
            with app.app_context():
                defaultCache.delete('cached_dataframe')
            
            dataFrame = db_utils.toDataframe("Select * FROM CoreB_Order;", 'app/Credentials/CoreB.json')
            data = dataFrame.to_dict('records')
        else:
            # Try to get cached Dataframe
            with app.app_context():
                data = cache1.get('cached_datafrane')
    
    page = request.args.get('page', 1, type=int)
    page, per_page, offset = get_page_args(page_parameter='page', 
                                           per_page_parameter='per_page')
    total = len(data)

    pagination_users = data[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=total)

    # use to prevent user from caching pages
    response = make_response(render_template('CoreB/main.html', data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str))
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
    raise NotImplementedError()