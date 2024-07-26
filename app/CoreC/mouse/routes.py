from datetime import datetime
from io import BytesIO

import mysql.connector as connection
import pandas as pd
import pymysql
from app import login_required
from app.CoreC.mouse import bp
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

@bp.route('/mouse', methods=['GET', 'POST'])
@login_required(role=["user", "coreC"])
def mouse():
    if request.method == 'POST':
        raise NotImplementedError()
    
    if request.method == 'GET':
        df = db_utils.toDataframe("SELECT * FROM Mouse_Stock", 'app/Credentials/CoreC.json')
        df.rename(columns={'PI_Name': 'PI', 'Mouse_Description': 'Description', 'Times_Back_Crossed': 'Times Back Crossed', 'MTA_Required': 'MTA Required',}, inplace=True)
        print(f"Mouse Dataframe: {df}")
        data = df.to_dict('records')
        print(f"Mouse Dictionary: {data}")

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