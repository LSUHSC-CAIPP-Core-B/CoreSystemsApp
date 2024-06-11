from flask import Flask, render_template, request, redirect, send_file, url_for, flash, make_response, send_from_directory
from flask_paginate import Pagination, get_page_args
import pandas as pd
from app.CoreB.orders import bp
from app.reader import Reader, find
from app.models import Invoice
from app import login_required
from app import db
from flask_caching import Cache
import redis
from io import BytesIO

reader = Reader("CAIPP_Order.csv")
information_reader = Reader("PI_ID - PI_ID.csv")

r = redis.Redis(decode_responses=True)

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
    # variable to hold CSV data
    data = reader.getFormattedDataCSV()

    if request.method == 'POST':
         # Clear the cache when new filters are applied
        with app.app_context():
            cache1.delete('cached_data')

        # search vars
        service_type = request.form.get('service_type') or ""
        pi_name = request.form.get('pi_name') or ""
        sort = request.form.get('sort') or "Original"
        # filter dict
        data = [dict for dict in data if dict['Service Type'].__contains__(service_type)]
        data = [dict for dict in data if dict['PI Name'].lower().__contains__(pi_name.lower())]
        # sort dict
        if sort != "Original":
            if sort == 'Request Date':
                data = sorted(data, key=lambda d: d[sort], reverse=True)
            else:
                data = sorted(data, key=lambda d: d[sort])
        with app.app_context():
            cache1.set('cached_data', data, timeout=3600)  # Cache for 1 hour (3600 seconds)

    # to always sort by newest date
    if request.method == "GET":
        with app.app_context():
            cached_data = cache1.get('cached_data')

        if cached_data is None:
            with app.app_context():
                defaultCache.delete('cached_dataframe')

            sort = "Request Date"
            data = sorted(data, key=lambda d: d[sort], reverse=True)

            with app.app_context():
                defaultCache.set('cached_dataframe', data, timeout=3600)
        else:
            # Try to get the cached DataFrame
            with app.app_context():
                data = cache1.get('cached_data')

    page, per_page, offset = get_page_args(page_parameter='page', 
                                           per_page_parameter='per_page')
    total = len(data)

    pagination_users = data[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=total)

    if request.method == 'GET':
        if r.get("download_refresh") == "True":
           flash('Please refresh download script')
        
        # use to prevent user from caching pages
        response = make_response(render_template('main.html', data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

    elif request.method == 'POST':
        return render_template('main.html', data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str)

@bp.route('/update', methods=['GET', 'POST'])
@login_required(role=["admin", "coreB"])
def update():
    """
    GET: Display edit screen of specified order
    POST: Update values of specified order
    """
    # HTTP GET method
    if request.method == 'GET':
        # variable to hold CSV data
        data = reader.getFormattedDataCSV()

        question_id = request.args.get('question_id')
        data = [dict for dict in data if dict['Question'].__contains__(question_id)]
        update_data = data[0]

        return render_template('update.html', fields = update_data)
  
    elif request.method == 'POST':
        # variable to hold CSV data
        data, unprocessed_df = reader.getFormattedDataCSV(withRaw=True)

        # updated row
        row = {}
        
        for key, val in dict(request.form).items():
            row[key] = val

        order_num = request.args.get('order_num')
        question_id = request.args.get('question_id')
        id = find(data, "Question", question_id)

        if id != None:
            data[int(id)] = row
            # change IDs in invoices
            invoices = Invoice.query.filter_by(project_id = order_num).all()
            if invoices != None:
                for invoice in invoices:
                    invoice.project_id = row["Project ID"]
                db.session.commit()
        # Error if id None
        else:
            return redirect(url_for('orders.orders'))

        reader.saveDataCSV(data, unprocessed_df)

        with app.app_context():
            cache1.delete('cached_data')
        with app.app_context():
            cache1.set('cached_data', data, timeout=3600)  # Cache for 1 hour (3600 seconds)

        return redirect(url_for('orders.orders'))

@bp.route('/delete', methods=['GET'])
@login_required(role=["admin", "coreB"])
def delete():
    """
    GET: Delete order
    """
    if request.method == 'GET':
        # variable to hold CSV data
        data = reader.getFormattedDataCSV()
        unprocessed_df = reader.getRawDataCSV(headers=True)
        question_id = request.args.get('question_id')

        # id has to be +2 to match CAIPP_Order.csv format
        id = find(data, "Question", question_id)
        if id != None:
            id = id + 2
        # Error if id None
        else:
            return redirect(url_for('orders.orders'))

        reader.deleteDataCSV(unprocessed_df, id)

        return redirect(url_for('orders.orders'))
    
@bp.route('/downloadOrdersCSV', methods=['GET'])
@login_required(role=["coreB"])
def downloadCSV():
    with app.app_context():
        saved_data = cache1.get('cached_dataframe')
    
    if saved_data is None:
        with app.app_context():
            saved_data = defaultCache.get('cached_dataframe')

    df = pd.DataFrame.from_dict(saved_data)
    csv = df.to_csv(index=False)
    
    # Convert the CSV string to bytes and use BytesIO
    csv_bytes = csv.encode('utf-8')
    csv_io = BytesIO(csv_bytes)
    
    return send_file(csv_io, mimetype='text/csv', as_attachment=True, download_name='Orders.csv')