from flask import (Flask, flash, make_response, redirect,
                   render_template, request, send_file, url_for)
from flask_caching import Cache
from flask_login import current_user
from flask_paginate import Pagination, get_page_args

from app import login_required
from app.CoreC.mouse import bp
from app.CoreC.mouse.mouseTable import mouseTable
from app.utils.db_utils import db_utils
from app.utils.logging_utils.logGenerator import Logger

# mouse object
mouseTable = mouseTable()

# Cache setup
app = Flask(__name__)
cache1 = Cache(app, config={'CACHE_TYPE': 'simple'}) # Memory-based cache
defaultCache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Logging set up
logFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LogGenerator = Logger(logFormat=logFormat, logFile='application.log')
logger = LogGenerator.generateLogger()

@bp.route('/mouse', methods=['GET', 'POST'])
@login_required(role=["user", "coreC"])
def mouse():
    """
    Handle the `/mouse` route to display and filter mouse data.

    **Methods:**
        - `GET`: Retrieve and paginate cached mouse data or load from the database if not cached.
        - `POST`: Apply filters from form inputs, sort the results, and update the cache with the filtered data.

    **Caching:**
        - Filtered data is cached for 1 hour under `cached_dataframe`.
        - Clears the cache when new filters are applied.

    **Response:**
        - Renders the `CoreC/mouse_stock.html` template with the paginated mouse data.
        - Implements pagination and prevents client-side caching with appropriate headers.
    """
    if request.method == 'POST':
        rawInputs = request.form

        inputDict = rawInputs.to_dict()
        Uinputs = list(inputDict.values())

        sort = inputDict["sort"]

        Uinputs.pop(-1)

        # ! For excepting raise ValueError(ValueError: Cannot set a DataFrame with multiple columns to the single column PI_Name_ratio
        try:
            data: dict = mouseTable.display(Uinputs, sort)
        except ValueError:
            flash(' No records to filter')
            return redirect(url_for('mouse.mouse'))

        with app.app_context():
            cache1.delete('cached_dataframe') # Clear the cache when new filters are applied
            cache1.set('cached_dataframe', data, timeout=3600)  # Cache for 1 hour (3600 seconds)
    
    if request.method == 'GET':
        with app.app_context():
            cached_data = cache1.get('cached_dataframe')
        
        if cached_data is None:
            with app.app_context():
                defaultCache.delete('cached_dataframe')

            df = db_utils.toDataframe("SELECT * FROM Mouse_Stock WHERE Genotype != 'N/A';", 'app/Credentials/CoreC.json')
            df.rename(columns={'PI_Name': 'PI', 'Mouse_Description': 'Description', 'Times_Back_Crossed': 'Times Back Crossed', 'MTA_Required': 'MTA Required'}, inplace=True)
        
            data = df.to_dict('records')

            with app.app_context():
                defaultCache.set('cached_dataframe', data, timeout=3600)
        else:
            # Try to get the cached DataFrame
            with app.app_context():
                data = cache1.get('cached_dataframe')

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
    
@bp.route('/addMouse', methods=['GET', 'POST'])
@login_required(role=["user", "coreC"])
def addMouse():
    """
    Handle the `/addMouse` route to add a new mouse record to the stock.

    **Methods:**
        - `POST`: Validate and add new mouse data. 
          Ensures no empty fields and ensures `Times Back Crossed` is a number. 
          Updates the mouse stock data and renders the updated stock page.
        - `GET`: Display an empty form for adding new mouse data.

    **Response:**
        - If successful, renders the `CoreC/mouse_stock.html` template with paginated mouse data.
        - Prevents client-side caching with appropriate headers.
    """
    if request.method == 'POST':
        inputs = request.form
        
        inputData = inputs.to_dict()

        has_empty_value = any(value == "" or value is None for value in inputData.values())
        
        if has_empty_value:
            flash('Fields cannot be empty')
            return redirect(url_for('mouse.addMouse'))
        
        if not inputData["Times Back Crossed"].isdigit():
            flash('"Times Back Crossed" must be a number')
            return redirect(url_for('mouse.addMouse'))

        df = mouseTable.add(inputData)
        df.rename(columns={'PI_Name': 'PI', 'Mouse_Description': 'Description', 'Times_Back_Crossed': 'Times Back Crossed', 'MTA_Required': 'MTA Required'}, inplace=True)
        data = df.to_dict(orient='records')
        
        page, per_page, offset = get_page_args(page_parameter='page', 
                                           per_page_parameter='per_page')
        
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
    
    if request.method == 'GET':
        data = {
            "PI": "",
            "Genotype": "",
            "Description": "",
            "Strain": "",
            "Times Back Crossed": "",
            "MTA Required": "",
        }

        # use to prevent user from caching pages
        response = make_response(render_template('CoreC/add_mouse.html', fields = data))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    
@bp.route('/changeMouse', methods=['GET', 'POST'])
@login_required(role=["user", "coreC"])
def changeMouse():
    """
    Handle the `/changeMouse` route to update an existing mouse record.

    **Methods:**
        - `POST`: Validates and updates the mouse data. 
          Ensures no empty fields and ensures that `Times Back Crossed` is a number. 
          Redirects to the mouse stock page after updating.
        - `GET`: Display a form pre-filled with the details of the mouse record to be updated.

    **Response:**
        - If successful, redirects to the `mouse` page.
        - Renders the `CoreC/change_mouse.html` template for GET requests.
        - Prevents client-side caching with appropriate headers.
    """
    if request.method == 'POST':
        inputs = request.form
            
        inputData = inputs.to_dict()

        has_empty_value = any(value == "" or value is None for value in inputData.values())
        
        if has_empty_value:
            flash('Fields cannot be empty')
            return redirect(url_for('mouse.addMouse'))
        
        if not inputData["Times Back Crossed"].isdigit():
            flash('"Times Back Crossed" must be a number')
            return redirect(url_for('mouse.addMouse'))

        #Executes change query
        mouseTable.change(inputData)

        # use to prevent user from caching pages
        response = make_response(redirect(url_for('mouse.mouse')))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    
    if request.method == 'GET':
        primary_key = request.args.get('primaryKey')
        query = "SELECT * FROM Mouse_Stock WHERE Stock_ID = %s;"
        df = db_utils.toDataframe(query, 'app/Credentials/CoreC.json', params=(primary_key,))
        df.rename(columns={'PI_Name': 'PI', 'Mouse_Description': 'Description', 'Times_Back_Crossed': 'Times Back Crossed', 'MTA_Required': 'MTA Required'}, inplace=True)

        data = df.to_dict()
        
        # use to prevent user from caching pages
        response = make_response(render_template('CoreC/change_mouse.html', fields = data, pkey = primary_key))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response
    
@bp.route('/deleteMouse', methods=['POST'])
@login_required(role=["user", "coreC"])
def deleteMouse():
    """
    Handle the `/deleteMouse` route to delete a mouse record.

    **Methods:**
        - `POST`: Delete the mouse record specified by the `primaryKey` field.

    **Response:**
        - Redirects to the `mouse` page after deletion.
        - Prevents client-side caching with appropriate headers.
    """
    primary_key = request.form['primaryKey']

    logger.info("Deletion Attempting...")

    mouseTable.delete(primary_key)

    # use to prevent user from caching pages
    response = make_response(redirect(url_for('mouse.mouse')))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

@bp.route('/downloadMouseCSV', methods=['GET'])
@login_required(role=["user", "coreC"])
def downloadCSV():
    num_rows = int(request.args.get('num_rows'))
    print(f"\nNumber of rows: {num_rows}\n")
    with app.app_context():
        saved_data = cache1.get('cached_dataframe')
    
    if saved_data is None:
        with app.app_context():
            saved_data = defaultCache.get('cached_dataframe')
        
    if num_rows == 0:
        print('\nDatabase Empty\n')
        flash(' No records to download')
        return redirect(url_for('mouse.mouse'))
    elif num_rows > 0:
        print('\nDatabase not empty\n')
        csv_io = mouseTable.download_CSV(saved_data=saved_data, dropCol=['Stock_ID', 'user_id'])
    
        return send_file(csv_io, mimetype='text/csv', as_attachment=True, download_name='Mouse Data.csv')