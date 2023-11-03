from flask import render_template, request, redirect, url_for, flash, make_response, send_from_directory
from flask_paginate import Pagination, get_page_args
from app.CoreB.orders import bp
from app.reader import Reader
from app import login_required
from app import db

reader = Reader("CAIPP_Order.csv")
information_reader = Reader("PI_ID - PI_ID.csv")


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
        if sort != 'Original':
            data = sorted(data, key=lambda d: d[sort])

    page, per_page, offset = get_page_args(page_parameter='page', 
                                           per_page_parameter='per_page')
    total = len(data)

    pagination_users = data[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=total)

    if request.method == 'GET':
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

        order_num = request.args.get('order_num')
        data = [dict for dict in data if dict['Project ID'].__contains__(order_num)]
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
        id = find(data, "Project ID", order_num)

        if id != None:
            data[int(id)] = row
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
        unprocessed_df = reader.getRawDataCSV()
        order_num = request.args.get('order_num')

        # id has to be +2 to match CAIPP_Order.csv format
        id = find(data, "Project ID", order_num)
        if id != None:
            id = id + 2
        # Error if id None
        else:
            return redirect(url_for('orders.orders'))

        reader.deleteDataCSV(unprocessed_df, id)

        return redirect(url_for('orders.orders'))

@bp.route('/information', methods=['GET'])
@login_required(role=["admin", "coreB"])
def information():
    if request.method == 'GET':
        # get PI list data
        data = information_reader.getRawDataCSV(headers=True, dict=True)
        order_num = request.args.get('order_num').split("_")[0]

        # get specific PI data
        data = [dict for dict in data if dict['PI ID'].lower().__contains__(order_num.lower())]
        #if len(data) == 0:
        #else:
        pi_data = data[0]

        # use to prevent user from caching pages
        response = make_response(render_template('information.html', data=pi_data, order_num=order_num, list=list, len=len, str=str))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    
        #return render_template('information.html', data=pi_data, order_num=order_num, list=list, len=len, str=str)

@bp.route('/pilist', methods=['GET', 'POST'])
@login_required(role=["admin"])
def pilist():
    # get PI list data
    data = information_reader.getRawDataCSV(headers=True, dict=True)

    if request.method == 'POST':
        # search vars
        department = request.form.get('department') or ""
        pi_name = request.form.get('pi_name') or ""
        # filter dict
        data = [dict for dict in data if dict['Department'].lower().__contains__(department.lower())]
        data = [dict for dict in data if dict['PI full name'].lower().__contains__(pi_name.lower())]
        sort = request.form.get('sort') or "Original"
        # sort dict
        if sort != 'Original':
            data = sorted(data, key=lambda d: d[sort])

        # TODO error while data empty, show diff screen

    page, per_page, offset = get_page_args(page_parameter='page', 
                                        per_page_parameter='per_page')
    total = len(data)

    pagination_users = data[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=total)

    # use to prevent user from caching pages
    response = make_response(render_template('pi_list.html', data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

    #return render_template('pi_list.html', data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str)