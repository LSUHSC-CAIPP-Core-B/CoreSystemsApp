from flask import render_template, request, redirect, url_for
from flask_login import login_required
from app.CoreB.graphs import bp

from app.reader import Reader

#reader = Reader("CAIPP_Order.csv")

@bp.route('/graphs', methods=['GET'])
@login_required
def graphs():
    if request.method == 'GET':
        return render_template('graphs.html')