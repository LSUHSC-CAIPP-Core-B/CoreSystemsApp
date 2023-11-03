from flask import render_template, request, redirect, url_for, flash
from flask_paginate import Pagination, get_page_args
from app.CoreC.stock import bp
from app.reader import Reader
from app import login_required

#information_reader = Reader("PI_ID - PI_ID.csv")

@bp.route('/stock', methods=['GET'])
@login_required(role=["user", "coreC"])
def stock():
    if request.method == 'GET':
        return render_template('stock.html')

