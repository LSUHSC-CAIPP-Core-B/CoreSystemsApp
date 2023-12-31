from flask import render_template, request, redirect, url_for, flash, make_response, send_from_directory
from flask_paginate import Pagination, get_page_args
from app.CoreB.pi_list import bp
from app.reader import Reader
from app import login_required

information_reader = Reader("PI_ID - PI_ID.csv")

@bp.route('/information', methods=['GET'])
@login_required(role=["admin", "coreB"])
def information():
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

@bp.route('/add_pi', methods=['GET', 'POST'])
@login_required(role=["admin"])
def add_pi():
    if request.method == 'GET':
        pi_data = {
            "PI_first_name": "",
            "PI_last_name": "",
            "PI_ID": "",
            "PI_email": "",
            "PI_departmnet": ""
        }
        # use to prevent user from caching pages
        response = make_response(render_template('add_pi.html', fields = pi_data))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

    elif request.method == 'POST':
        first_name = request.form.get('PI_first_name')
        last_name = request.form.get('PI_last_name')
        pi_id = request.form.get('PI_ID')
        email = request.form.get('PI_email')
        department = request.form.get('PI_departmnet')

        # fields cannot be empty
        if first_name == "" or last_name == "" or pi_id == "" or email == "" or department == "":
            flash('Fields cannot be empty')
            return redirect(url_for('pi_list.add_pi'))
        
        # get csv data
        data = information_reader.getRawDataCSV(headers=True, dict=True)

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