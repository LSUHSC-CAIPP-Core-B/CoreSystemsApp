from flask import render_template, request, redirect, url_for, flash, make_response
from flask_paginate import Pagination, get_page_args
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Role
from app.auth import bp
from app import db, login_required

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET: Display login page
    POST: Login user
    """
    if request.method == 'GET':
        return render_template('login.html')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        # check if the user actually exists
        # take the user-supplied password, hash it, and compare it to the hashed password in the database
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('auth.login')) # if the user doesn't exist or password is wrong, reload the page
        
        login_user(user)

        # checl what roles the user has and redirect him to desired page
        roles_to_check = []
        for r in user.urole:
            roles_to_check.append(r.role)

        if "coreB" in roles_to_check:
            return redirect(url_for('orders.orders'))
        elif "coreC" in roles_to_check:
            return redirect(url_for('antibodies.antibodies_route'))

@bp.route('/signup', methods=['GET', 'POST'])
@login_required(role=["admin"])
def signup():
    """
    GET: Display admin panel
    POST: Add new user
    """
    if request.method == 'GET':
        # get all admin users
        users = User.query.all()

        page, per_page, offset = get_page_args(page_parameter='page', 
                                           per_page_parameter='per_page')
        total = len(users)

        pagination_users = users[offset: offset + per_page]
        pagination = Pagination(page=page, per_page=per_page, total=total)

        # use to prevent user from caching pages
        response = make_response(render_template('signup.html', users=pagination_users, page=page, per_page=per_page, pagination=pagination))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    
    elif request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        core = request.form.get('core')
        permision = request.form.get('permision')

        if email == "" or name == "" or password == "":
            flash('Fields cannot be empty')
            return redirect(url_for('auth.signup'))

        user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

        if user: # if a user is found, we want to redirect back to signup page so user can try again
            flash('Email address already exists')
            return redirect(url_for('auth.signup'))

        # create a new user with the form data. Hash the password so the plaintext version isn't saved.
        new_user = User(email=email, name=name, password=generate_password_hash(password, method='pbkdf2'))

        # add roles
        if permision.__contains__("a"):
            new_user.urole.append(Role.query.filter_by(role="admin").first())
            new_user.urole.append(Role.query.filter_by(role="user").first())
        elif permision.__contains__("u"):
            new_user.urole.append(Role.query.filter_by(role="user").first())
        if core.__contains__("B"):
            new_user.urole.append(Role.query.filter_by(role="coreB").first())
        if core.__contains__("C"):
            new_user.urole.append(Role.query.filter_by(role="coreC").first())

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('auth.login'))
    
@bp.route('/deleteUser', methods=['GET'])
@login_required(["admin"])
def delete_user():
    """
    GET: Delete user
    """
    if request.method == 'GET':
        email = request.args['email']

        user = User.query.filter_by(email=email).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            return redirect(url_for('auth.signup'))
        
        return redirect(url_for('auth.signup'))


@bp.route('/logout')
@login_required(["any"])
def logout():
    """
    Delete user
    """
    logout_user()
    # Delete rememberme cookie because logout_user does not do it for you.
    response = make_response(redirect(url_for('auth.login')))
    response.delete_cookie('remember_token') 
    return response