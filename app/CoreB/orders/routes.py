from flask import render_template, request, redirect, url_for, flash, make_response, send_from_directory
from flask_paginate import Pagination, get_page_args
from app.CoreB.orders import bp
from app.reader import Reader
from app.models import Invoice
from app import login_required
from app import db
import redis

reader = Reader("CAIPP_Order.csv")
information_reader = Reader("PI_ID - PI_ID.csv")

r = redis.Redis(decode_responses=True)


def find(lst, key, value):
    """
    Find dict in list of dicts that have a specified value of specified key

    lst (list(dict)): list of dicts to check in
    key (str): key of which value to check
    value (var): value to look for in dict in key

    return: index of found dict in list or None if nothing found
    """
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return None

@bp.route('/orders', methods=['GET', 'POST'])
@login_required(role=["user", "coreB"])
def orders():
    # variable to hold CSV data
    data = reader.getFormattedDataCSV()

    if request.method == 'POST':
        # search vars
        service_type = request.form.get('service_type') or ""
        pi_name = request.form.get('pi_name') or ""
        sort = request.form.get('sort') or "Original"
        # filter dict
        data = [dict for dict in data if dict['Service Type'].__contains__(service_type)]
        data = [dict for dict in data if dict['PI Name'].lower().__contains__(pi_name.lower())]
        # sort dict
        if sort != 'Request Date':
            data = sorted(data, key=lambda d: d[sort])
        else:
            print(type(data[0]["Request Date"]))
            data = sorted(data, key=lambda d: d[sort], reverse=True)

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
        #return render_template('main.html', data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str)

    elif request.method == 'POST':
        return render_template('main.html', data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str)

@bp.route('/update', methods=['GET', 'POST'])
@login_required(role=["admin", "coreB"])
def update():
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
        return redirect(url_for('orders.orders'))

@bp.route('/delete', methods=['GET'])
@login_required(role=["admin", "coreB"])
def delete():
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