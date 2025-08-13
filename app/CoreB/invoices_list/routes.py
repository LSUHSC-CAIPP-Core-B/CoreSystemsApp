from io import BytesIO
from flask import Flask, render_template, request, make_response, send_file, send_from_directory, flash, redirect, url_for
from flask_caching import Cache
from flask_paginate import Pagination, get_page_args
import pandas as pd
import pymysql
from sqlalchemy import create_engine, text
import urllib
from app.CoreB.invoices_list import bp
from app import login_required
from app.models import Invoice
from app import db
from datetime import datetime
from app.pdfwriter import PdfWriter
from app.reader import Reader
import numpy as np
from app.utils.db_utils import db_utils

app = Flask(__name__)
cache1 = Cache(app, config={'CACHE_TYPE': 'simple'}) # Memory-based cache
defaultCache = Cache(app, config={'CACHE_TYPE': 'simple'})

pdfWriter = PdfWriter("app/static/invoice-base.pdf","app/static/filled-out-v2.pdf")

def list_services(services_str, services_to_find):
    """
    Find what services are requested

    services_str (str): string with services requested
    services_to_find (list(str)): list of possible services to find

    return (list(str)): list of services found 
    """
    services = []

    for service_to_find in services_to_find:
        if services_str.__contains__(service_to_find["Service"]):
            services.append(service_to_find)
    
    return services

@bp.route('/invoice', methods=['POST'])
@login_required(role=["admin", "coreB"])
def invoice():
    """
    POST: Provide data to generate invoice
    """
    if request.method == 'POST':
        # get order data to input automatically into invoice (passed to POST)
        order_num = request.form.get('order_num')
        pi_name = request.form.get('pi_name')
        bm_info = request.form.get('bm_info')
        service_type = request.form.get('service_type')
        services_str = request.form.get('services')
        sample_num = request.form.get('sample_num')
        # get account number and manager name from bm_info field (format: acc_num,additional info)
        bm_info_split = bm_info.split(",")

        # check if bm info format is correct
        if len(bm_info_split) != 3:
            return render_template('CoreB/error_invoice.html', error_msg="Please correct Account number and billing contact person format (account number, manager name, phone number)")
        acc_num = bm_info_split[0]
        manager_name = bm_info_split[1]

        # check what services are selected and put them into array       
        # if service is BioRender license then make service_str the same as service_type to work the same way as the other servies
        if service_type == "BioRender license":
            biorender_accounts = services_str
            services_str = service_type
            # pass dict with hidden data just to pass it to the next request
            hidden_data = {
                "Account Number": acc_num,
                "Quantity" : sample_num,
                "Order Number": order_num,
                "Manager Name": manager_name,
                "PI Name": pi_name,
                "BioRender Accounts": biorender_accounts
            }
        else:
            # pass dict with hidden data just to pass it to the next request
            hidden_data = {
                "Account Number": acc_num,
                "Quantity" : sample_num,
                "Order Number": order_num,
                "Manager Name": manager_name,
                "PI Name": pi_name
            }

        query = f"SELECT * FROM Invoice WHERE project_id = '{order_num}'"
        df = db_utils.toDataframe(query, 'app/Credentials/CoreB.json')

        if df.empty:
            #last_invoice_row = db_utils.execute("SELECT * FROM Invoice ORDER BY id DESC LIMIT 1;", 'app/Credentials/CoreB.json')
            last_invoice_row = db_utils.toDataframe("SELECT * FROM Invoice ORDER BY id DESC LIMIT 1;", 'app/Credentials/CoreB.json')
            latest_id = last_invoice_row["id"].iloc[0]

            new_invoice_data = {
                "id": [latest_id+1], # Get the next incremented number for the table
                "project_id": [order_num],
                "service_type": ["ASSIGN"],
                "service_sample_number": [0],
                "service_sample_price": [0],
                "total_price": [0],
                "discount_sample_number": [0],
                "discount_sample_amount": [0],
                "discount_reason": ["ASSIGN"],
                "total_discount": [0],
            }

            invoice_to_add = pd.DataFrame(new_invoice_data)

            db_config = db_utils.json_Reader('app/Credentials/CoreB.json')
            host = db_config['host']
            database = db_config['database']
            user = db_config['user']
            password = urllib.parse.quote_plus(db_config['password'])

            db_connection_str = f'mysql+mysqlconnector://{user}:{password}@{host}/{database}'
            engine = create_engine(db_connection_str)

            invoice_to_add.to_sql("Invoice", engine, schema='CoreB', if_exists='append', index=False)
            invoices = invoice_to_add.to_dict(orient='records')
        else:
            invoices  = df.to_dict(orient='records')

        total_price_sum = sum(inv["total_price"] for inv in invoices if inv["service_type"] != "All services discount")
        discount_row = next((inv for inv in invoices if inv["service_type"] == "All services discount"), None)
        percent_discount = (discount_row["total_discount"] / total_price_sum * 100.0) if total_price_sum and discount_row else 0

        response = make_response(render_template('CoreB/edit_invoice.html', order_num = order_num, service_type = service_type, sample_num = sample_num, fields_hidden = hidden_data, invoices=invoices, percent_discount=percent_discount, len=len))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

@bp.route('/gen_invoice', methods=['POST'])
@login_required(role=["admin", "coreB"])
def gen_invoice(): 
    """
    POST: Generate invoice PDF file
    """
    if request.method == 'POST':
        order_num = request.form.get("Order Number", "")
        pi_name = request.form.get('PI Name', "")
        pi_name_line = f"Service for {pi_name}"
        acc_num = request.form.get('Account Number', "")
        manager_name = request.form.get('Manager Name', "")
        services_num = int(request.form.get('Services Number', 0))
        biorender_accounts = request.form.get('BioRender Accounts', "")
        date = datetime.now().strftime('%m/%d/%Y')

        dict_data = {
            'DEBIT ACCOUNTRow1': acc_num,
            'DEPT REQUISITION Row1': order_num,
            'Date5_af_date': date,
            'CARE OFRow1': manager_name,
            'DESCRIPTIONRow2': pi_name_line
        }

        # Initialize
        service_row = 4
        item_number = 1
        grand_total = 0.0
        grand_total_discount = 0.0

        # Load service list that should not be charged per sample
        services_no_unit_price_df = pd.read_csv("services_with_no_unit_price.csv")
        services_no_unit_price = services_no_unit_price_df["Service"].tolist()

        # Process each service
        for i in range(services_num):
            # Get form fields
            name = request.form.get(f"service {i} name")
            qty = float(request.form.get(f"service {i} qty") or 0)
            discount_reason = request.form.get(f"service {i} discount reason", "")
            discount_qty = float(request.form.get(f"service {i} discount qty") or 0)
            discount_amt = float(request.form.get(f"service {i} discount amount") or 0)
            price = float(request.form.get(f"service {i} price") or 0)

            # Set the discount row to render last
            if name == "All services discount":
                service_row = 21

            # Fill dict_data for PDF generation
            if name != "All services discount":
                # Service row
                dict_data[f"ITEM Row{service_row}"] = str(item_number)
                dict_data[f"QTYRow{service_row}"] = str(qty)
                dict_data[f"UNITRow{service_row}"] = "ea"
                dict_data[f"DESCRIPTIONRow{service_row}"] = name
                dict_data[f"UNIT COSTRow{service_row}"] = f"$ {price}"

                total = price if name in services_no_unit_price else price * qty
                dict_data[f"TOTALRow{service_row}"] = f"$ {total}"
                grand_total += total
            else:
                total = 0

            # Discount row
            if discount_reason:
                if name == "All services discount":
                    discount_amt = grand_total * (discount_amt / 100.0)
                    discount_qty = 1
                total_discount = discount_amt * discount_qty
                dict_data[f"ITEM Row{service_row + 1}"] = str(item_number + 1)
                dict_data[f"QTYRow{service_row + 1}"] = str(discount_qty)
                dict_data[f"UNITRow{service_row + 1}"] = "ea"
                dict_data[f"DESCRIPTIONRow{service_row + 1}"] = discount_reason
                dict_data[f"UNIT COSTRow{service_row + 1}"] = f"-$ {discount_amt}"
                dict_data[f"TOTALRow{service_row + 1}"] = f"-$ {total_discount}"
                grand_total_discount += total_discount
            else:
                total_discount = 0

            db_utils.execute("""
                UPDATE Invoice SET
                    service_sample_number = %(qty)s,
                    service_sample_price = %(price)s,
                    total_price = %(total)s,
                    discount_sample_number = %(discount_qty)s,
                    discount_sample_amount = %(discount_amt)s,
                    discount_reason = %(discount_reason)s,
                    total_discount = %(total_discount)s
                WHERE project_id = %(order_num)s AND service_type = %(service_type)s
            """, 'app/Credentials/CoreB.json', params={
                "qty": qty,
                "price": price,
                "total": total,
                "discount_qty": discount_qty,
                "discount_amt": discount_amt,
                "discount_reason": discount_reason,
                "total_discount": total_discount,
                "order_num": order_num,
                "service_type": name
            })


            service_row += 2
            item_number += 2

        # Final grand total
        dict_data["TOTALGRAND TOTAL"] = f"$ {grand_total - grand_total_discount}"

        # Add BioRender accounts if any
        if biorender_accounts:
            dict_data["DESCRIPTIONRow6"] = "License for"
            for idx, account in enumerate(biorender_accounts.split(",")):
                dict_data[f"DESCRIPTIONRow{7 + idx}"] = account.strip()

        pdfWriter.fillForm(dict_data)
        return send_from_directory('static', "filled-out-v2.pdf")

@bp.route('/invoices_list', methods=['GET', 'POST'])
@login_required(role=["coreB", "admin"])
def invoices_list():
    """
    GET: Display list of all invoices made
    POST: Display filtered list of all invoices made
    """
    with app.app_context():
        cache1.delete('cached_data')

    query = f"SELECT * FROM Invoice"
    df = db_utils.toDataframe(query, 'app/Credentials/CoreB.json')

    if df.empty:
        data = []
    else:
        #Group by project_id and compute sums
        grouped = df.groupby("project_id").agg({
            "total_price": "sum",
            "total_discount": "sum"
        }).reset_index()
    
    # Compute final price
    grouped["final_price"] = grouped["total_price"] - grouped["total_discount"]

    #rename for display
    grouped = grouped.rename(columns={
        "project_id": "Project ID",
        "total_price": "Total price",
        "total_discount": "Total discount",
        "final_price": "Final price"
    })

    data = grouped.to_dict(orient="records")

    if request.method == 'POST':
        sort = request.form.get('sort') or "Original"
        # sort dict
        if sort != 'Original':
            if sort != 'Project ID':
                reverse = sort != "Project ID"
                data = sorted(data, key=lambda d: d[sort], reverse=reverse)
    
    with app.app_context():
        cache1.set('cached_data', data, timeout=3600)

    page, per_page, offset = get_page_args(page_parameter='page', 
                                        per_page_parameter='per_page')
    total = len(data)

    pagination_users = data[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=total)

    # use to prevent user from caching pages
    response = make_response(render_template("CoreB/invoices_list.html", data=pagination_users, page=page, per_page=per_page, pagination=pagination, list=list, len=len, str=str))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response

@bp.route('/invoice_details', methods=['GET'])
@login_required(["coreB", "admin"])
def invoice_details():
    """
    GET: Displays invoice information
    """
    if request.method == 'GET':
        project_id = request.args['project_id']

        query = f"SELECT service_type, total_price, total_discount FROM Invoice WHERE project_id = '{project_id}'"
        df = db_utils.toDataframe(query, 'app/Credentials/CoreB.json')

        df = df.rename(columns={
            "service_type": "Service",
            "total_price": "Total price",
            "total_discount": "Total discount"
        })

        invoice_details = df.to_dict(orient="records") if not df.empty else []


        # use to prevent user from caching pages
        response = make_response(render_template('CoreB/invoice_details.html', data=invoice_details, project_id=project_id, list=list, len=len, str=str))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

@bp.route('/delete_invoice', methods=['GET'])
@login_required(["coreB", "admin"])
def delete_invoice():
    """
    GET: Delete invoice
    """
    if request.method == 'GET':
        project_id = request.args['project_id']

        if project_id:
            mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreB.json'))
            cursor = mydb.cursor()

            # SQL DELETE query
            query = "DELETE FROM Invoice WHERE `project_id` = %s"

            #Execute SQL query
            cursor.execute(query, (project_id,))

            # Commit the transaction
            mydb.commit()

            # Close the cursor and connection
            cursor.close()
            mydb.close()
        
        response = make_response(redirect(url_for('invoices_list.invoices_list')))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
        response.headers["Pragma"] = "no-cache" # HTTP 1.0.
        response.headers["Expires"] = "0" # Proxies.
        return response

@bp.route('/downloadInvoicesCSV', methods=['GET'])
@login_required(role=["coreB"])
def downloadCSV():
    with app.app_context():
        saved_data = cache1.get('cached_data')
    
    if saved_data is None:
        with app.app_context():
            saved_data = defaultCache.get('cached_data')

    df = pd.DataFrame.from_dict(saved_data)
    csv = df.to_csv(index=False)
    
    # Convert the CSV string to bytes and use BytesIO
    csv_bytes = csv.encode('utf-8')
    csv_io = BytesIO(csv_bytes)
    
    return send_file(csv_io, mimetype='text/csv', as_attachment=True, download_name='Invoices.csv')